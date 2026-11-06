"""Separate-process SAC training, evaluation, resumption and trajectory export."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import shutil
import time

import numpy as np

from .environment import ReachEnv, load_config
from .experiments import (NumpyActor, config_signature, evaluate, export_actor,
                          rollout, write_json)


def saved_config(run):
    return load_config(Path(run) / 'config.json')


def train(args):
    import torch
    from stable_baselines3 import SAC
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.env_checker import check_env
    from stable_baselines3.common.logger import configure

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    config = saved_config(args.resume) if args.resume else load_config(args.config)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = ReachEnv(config)
    check_env(env, warn=True)
    signature = config_signature(config, env.model.sha256)
    shutil.copyfile(config['model'], output / 'model.urdf')
    write_json(output / 'config.json', dict(config, model='model.urdf'))
    write_json(output / 'manifest.json', {
        'schema': 'atom-rl-run-v1', 'seed': args.seed, 'model_sha256': env.model.sha256,
        'config_signature': signature, 'platform': platform.platform(),
        'python': platform.python_version(),
        'versions': {name: importlib.metadata.version(name)
                     for name in ('numpy', 'torch', 'gymnasium', 'stable-baselines3')},
        'resume_from': str(Path(args.resume).resolve()) if args.resume else None,
        'resume_semantics': 'optimizer/replay retained; new episode and RNG seed on resume',
        'validation_seeds': [100000, 100020], 'test_seeds': [200000, 200100],
    })
    monitored = Monitor(env, str(output / 'episodes.csv'),
                        info_keywords=('is_success', 'position_error_m', 'orientation_error_rad',
                                       'limit_violations', 'status'))
    if args.resume:
        manifest = json.loads((Path(args.resume) / 'manifest.json').read_text())
        if manifest['config_signature'] != signature:
            raise ValueError('Resume configuration does not match checkpoint')
        model = SAC.load(Path(args.resume) / 'final.zip', env=monitored, device='cpu', seed=args.seed)
        model.load_replay_buffer(Path(args.resume) / 'replay.pkl')
    else:
        settings = dict(config['training'])
        architecture = settings.pop('net_arch')
        model = SAC('MlpPolicy', monitored, seed=args.seed, device='cpu',
                    policy_kwargs={'net_arch': architecture}, train_freq=1, gradient_steps=1,
                    **settings)
    model.set_logger(configure(str(output / 'training'), ['csv']))
    write_json(output / 'before.json', evaluate(config, model, range(100000, 100020)))

    class Progress(BaseCallback):
        def __init__(self):
            super().__init__()
            self.best = (-1, -float('inf'))
            self.started = time.perf_counter()

        def _on_step(self):
            if self.n_calls % args.checkpoint_every == 0:
                result = evaluate(config, self.model, range(100000, 100020))
                summary = result['summary']
                record = dict(summary, timesteps=self.num_timesteps,
                              elapsed_s=time.perf_counter() - self.started)
                with (output / 'validation.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(record, allow_nan=False) + '\n')
                score = (summary['success_rate'], -summary['position_error_mean_m'])
                if score > self.best:
                    self.best = score
                    self.model.save(output / 'best.zip')
                    export_actor(self.model, output / 'best_actor.npz', config, env.model.sha256)
                self.model.save(output / 'checkpoint.zip')
                self.model.save_replay_buffer(output / 'checkpoint_replay.pkl')
                print(json.dumps(record), flush=True)
            return True

    started = time.perf_counter()
    interrupted = False
    try:
        model.learn(total_timesteps=args.steps, callback=Progress(),
                    reset_num_timesteps=not bool(args.resume), log_interval=10)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        model.save(output / 'final.zip')
        model.save_replay_buffer(output / 'replay.pkl')
        export_actor(model, output / 'actor.npz', config, env.model.sha256)
        write_json(output / 'training_result.json', {
            'timesteps': model.num_timesteps, 'training_wall_s': time.perf_counter() - started,
            'interrupted': interrupted,
        })
        monitored.close()
    print(f'Run saved: {output}', flush=True)


def compare(args):
    config = saved_config(args.run)
    env = ReachEnv(config)
    policy = NumpyActor(Path(args.run) / args.actor, config, env.model.sha256)
    seeds = range(args.seed_start, args.seed_start + args.episodes)
    result = {
        'schema': 'atom-paired-evaluation-v1', 'profile': config['profile'],
        'model_sha256': env.model.sha256, 'seed_start': args.seed_start,
        'policy': args.actor,
        'sac': evaluate(config, policy, seeds),
        'conventional': evaluate(config, 'conventional', seeds),
        'random': evaluate(config, 'random', seeds),
    }
    write_json(args.output, result)
    print(json.dumps({name: result[name]['summary'] for name in ('sac', 'conventional', 'random')},
                     indent=2))


def demo(args):
    config = saved_config(args.run)
    env = ReachEnv(config)
    policy = NumpyActor(Path(args.run) / args.actor, config, env.model.sha256)
    options = None
    if args.target_pose:
        options = {'target_pose': json.loads(Path(args.target_pose).read_text()),
                   'initial_q': env.model.center.tolist()}
    info, trajectory = rollout(env, policy, args.seed, options=options, trajectory=True)
    write_json(args.output, trajectory)
    print(json.dumps(info, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    training = commands.add_parser('train')
    source = training.add_mutually_exclusive_group(required=True)
    source.add_argument('--config')
    source.add_argument('--resume', help='Trusted local run with final.zip and replay.pkl')
    training.add_argument('--output', required=True)
    training.add_argument('--steps', type=int, default=50000)
    training.add_argument('--seed', type=int, default=7)
    training.add_argument('--checkpoint-every', type=int, default=5000)
    training.set_defaults(func=train)
    evaluation = commands.add_parser('evaluate')
    evaluation.add_argument('--run', required=True)
    evaluation.add_argument('--actor', default='actor.npz')
    evaluation.add_argument('--episodes', type=int, default=100)
    evaluation.add_argument('--seed-start', type=int, default=200000)
    evaluation.add_argument('--output', required=True)
    evaluation.set_defaults(func=compare)
    demonstration = commands.add_parser('demo')
    demonstration.add_argument('--run', required=True)
    demonstration.add_argument('--actor', default='actor.npz')
    demonstration.add_argument('--seed', type=int, default=300000)
    demonstration.add_argument('--target-pose', help='JSON 4x4 transform in root frame')
    demonstration.add_argument('--output', required=True)
    demonstration.set_defaults(func=demo)
    args = parser.parse_args()
    for name in ('steps', 'checkpoint_every', 'episodes'):
        if hasattr(args, name) and getattr(args, name) <= 0:
            parser.error(f'{name} must be positive')
    args.func(args)


if __name__ == '__main__':
    main()
