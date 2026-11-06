"""Train and evaluate an experimental pixel-only PPO grasp policy."""
import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import mujoco
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv
from atom_mujoco.training_monitor import RunRecorder, TrainingDisplay

from atom_mujoco.visual_grasp_env import VisualGraspEnv


def make_worker(bundle, horizon, stage, mirror):
    env = VisualGraspEnv(bundle, horizon=horizon, stage=stage)
    env.mirror_state = mirror
    return env


def evaluate(env, policy, seeds):
    results = []
    for seed in seeds:
        obs, _ = env.reset(seed=seed)
        total = 0.
        for _ in range(env.horizon):
            if policy is None:
                action = np.zeros(4, dtype=np.float32)
            else:
                action, _ = policy.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total += reward
            if terminated or truncated:
                break
        results.append(dict(seed=seed, return_value=total, **info))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=100000)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--eval-episodes', type=int, default=10)
    parser.add_argument('--device', choices=['cpu','cuda','auto'], default='auto')
    parser.add_argument('--horizon', type=int, default=100)
    parser.add_argument('--stage',choices=['lift','grasp'],default='lift')
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--speed',type=float,default=2.)
    initialization = parser.add_mutually_exclusive_group()
    initialization.add_argument('--warm-start', type=Path, help='Import weights with a fresh optimizer')
    initialization.add_argument('--resume',type=Path,help='Previous run directory; new output is required')
    parser.add_argument('--warm-start-features', action='store_true',
                        help='Transfer the visual encoder and initialize fresh policy heads')
    parser.add_argument('--workers', type=int, choices=range(1, 9), default=1)
    args = parser.parse_args()
    if args.warm_start_features and not args.warm_start:
        parser.error('--warm-start-features requires --warm-start')
    if args.steps<=0 or args.eval_episodes<=0 or args.horizon<=0 or not np.isfinite(args.speed) or args.speed<=0:
        parser.error('Positive steps, horizon and evaluation episodes required')
    if args.output.exists():
        parser.error('Use a new output directory')
    if args.device=='cuda' and not torch.cuda.is_available():
        parser.error('This PyTorch environment has no CUDA device')
    model_hash = hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest()
    config = dict(environment_version=VisualGraspEnv.VERSION, stage=args.stage,
                  horizon=args.horizon, model_sha256=model_hash)
    if args.stage == 'grasp':
        config['grasp_reset'] = 'fully_open_v1'
    lineage = None
    source = args.resume or args.warm_start
    if source:
        previous = json.loads((source/'run.json').read_text())['environment']
        previous_report = json.loads((source/'report.json').read_text())
        checkpoint_hash = hashlib.sha256((source/'policy.zip').read_bytes()).hexdigest()
        if previous_report['environment'] != previous or checkpoint_hash != previous_report['checkpoint_sha256']:
            parser.error('Source checkpoint or configuration differs from recorded result')
        expected = dict(config, stage=previous['stage']) if args.warm_start else config
        if args.warm_start and previous['stage'] != args.stage:
            expected.pop('grasp_reset', None)
            expected.update({key: previous[key] for key in ('grasp_reset',) if key in previous})
        if previous != expected:
            parser.error('Resume requires an identical environment; warm-start may change only stage')
        lineage = dict(mode='warm_start' if args.warm_start else 'resume',
                       source=str(source.resolve()), source_environment=previous,
                       source_checkpoint_sha256=checkpoint_hash,
                       source_steps=previous_report['trained_steps'])
        if args.warm_start:
            lineage['transfer_scope'] = 'features' if args.warm_start_features else 'policy'
    args.output.mkdir(parents=True)
    (args.output/'run.json').write_text(json.dumps(dict(environment=config,
        requested_steps=args.steps, seed=args.seed, watch=args.watch, workers=args.workers, initialization=lineage,
        resume=str(args.resume) if args.resume else None),indent=2)+'\n')
    torch.set_num_threads(2)
    started = time.perf_counter()
    env = VisualGraspEnv(args.bundle, horizon=args.horizon, stage=args.stage)
    display = None
    recorder = RunRecorder(args.output, workers=args.workers)
    parallel = None
    try:
        check_env(env, warn=True)
        if args.workers > 1:
            parallel = SubprocVecEnv([
                partial(make_worker, args.bundle, args.horizon, args.stage, args.watch and index == 0)
                for index in range(args.workers)
            ], start_method='spawn')
        training_env = parallel if parallel is not None else env
        policy = PPO('CnnPolicy',training_env,n_steps=128,batch_size=32,n_epochs=4,
                     learning_rate=3e-4,seed=args.seed,device=args.device,verbose=1)
        if args.resume:
            policy = PPO.load(args.resume/'policy.zip',env=training_env,device=args.device)
            policy.set_random_seed(args.seed)
        if args.warm_start:
            donor = PPO.load(source/'policy.zip', device='cpu')
            if donor.observation_space != policy.observation_space or donor.action_space != policy.action_space:
                parser.error('Warm-start requires identical observation and action spaces')
            source_module = donor.policy
            target_module = policy.policy
            if args.warm_start_features:
                source_module = source_module.features_extractor
                target_module = target_module.features_extractor
            weights = source_module.state_dict()
            target_module.load_state_dict(weights, strict=True)
            if not all(torch.equal(value, target_module.state_dict()[key].cpu()) for key, value in weights.items()):
                raise RuntimeError('Transferred weights differ from source')
            if policy.policy.optimizer.state or policy.num_timesteps:
                raise RuntimeError('Warm-start requires fresh optimizer and timestep counter')
            print('Warm-start weights verified: '+checkpoint_hash, flush=True)
            del donor, weights, source_module, target_module
        initial = {key:value.clone() for key,value in policy.policy.state_dict().items()}
        if args.watch:
            env.reset(seed=args.seed)
            display = TrainingDisplay(env,speed=args.speed,device=str(policy.device))
            if parallel is None:
                env.on_transition = display.update
        class Progress(BaseCallback):
            stopped = False

            def _on_step(self):
                for index, (reward, done, info) in enumerate(zip(
                        self.locals['rewards'], self.locals['dones'], self.locals['infos'])):
                    recorder.step(self.num_timesteps, reward, done, info, worker=index)
                if display:
                    display.step = self.num_timesteps
                    display.episodes = recorder.episodes
                    display.successes = recorder.successes
                    if parallel is None:
                        display.pump()
                    else:
                        info = self.locals['infos'][0]
                        with display.viewer.lock():
                            env.sim.data.qpos[:] = info['mirror_qpos']
                            mujoco.mj_forward(env.sim.model, env.sim.data)
                        pixels = info.get('terminal_observation', self.locals['new_obs'][0])
                        display.update(pixels, info)
                if self.num_timesteps // 2048 > (self.num_timesteps-args.workers) // 2048:
                    self.model.save(args.output/f'checkpoint-{self.num_timesteps}')
                self.stopped = bool(display and display.stopped) or (args.output/'STOP').exists()
                return not self.stopped
        interrupted = False
        progress = Progress()
        try:
            policy.learn(total_timesteps=args.steps,callback=progress,reset_num_timesteps=not bool(args.resume))
        except KeyboardInterrupt:
            interrupted = True
        except Exception:
            policy.save(args.output/'failed-policy')
            recorder.progress(policy.num_timesteps,'failed')
            raise
        interrupted = interrupted or progress.stopped
        env.on_transition = None
        if display:
            display.close()
            display = None
        recorder.progress(policy.num_timesteps,'stopped' if interrupted else 'evaluating')
        policy.save(args.output/'policy')
        changed = any(not torch.equal(value,policy.policy.state_dict()[key]) for key,value in initial.items())
        seeds = list(range(10000,10000+args.eval_episodes))
        learned = [] if interrupted else evaluate(env,policy,seeds)
        hold = [] if interrupted else evaluate(env,None,seeds)
        loaded = PPO.load(args.output/'policy.zip',device=args.device)
        obs,_ = env.reset(seed=seeds[0])
        a,_ = policy.predict(obs,deterministic=True)
        b,_ = loaded.predict(obs,deterministic=True)
        assert np.allclose(a,b), 'Checkpoint reload changed deterministic action'
        report = dict(schema=2, environment=config, workers=args.workers, initialization=lineage, interrupted=interrupted, algorithm='PPO', observation='96x96 RGB only',
            task='local E2 pawn '+args.stage, reward_source='simulation_oracle',
            model_parameters_updated=changed, trained_steps=policy.num_timesteps,
            cuda_available=torch.cuda.is_available(), device=str(policy.device),
            torch_version=torch.__version__, seed=args.seed,
            gpu_name=torch.cuda.get_device_name(0) if policy.device.type=='cuda' else None,
            wall_time_s=time.perf_counter()-started,
            model_sha256=hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest(),
            checkpoint_sha256=hashlib.sha256((args.output/'policy.zip').read_bytes()).hexdigest(),
            evaluation=learned, hold_baseline=hold,
            success_rate=float(np.mean([x['success'] for x in learned])) if learned else None,
            validated_for_playground=False)
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        recorder.progress(policy.num_timesteps,'stopped' if interrupted else 'completed')
        print(json.dumps(report,indent=2))
    finally:
        env.on_transition = None
        if display:
            display.close()
        if parallel is not None:
            parallel.close()
        env.close()


if __name__=='__main__':
    main()
