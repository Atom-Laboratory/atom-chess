"""Train, resume or evaluate the P038 native camera-guided residual environment."""
import argparse
from atom_mujoco.paths import new_run
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_checker import check_env

from atom_mujoco.camera_manipulation_env import CameraManipulationEnv


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def weights_sha(policy):
    digest = hashlib.sha256()
    for name, tensor in sorted(policy.policy.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def evaluate(env, policy, episodes, seed, viewer=None):
    records = []
    for index in range(episodes):
        targets = getattr(env, 'targets', [])
        options = dict(target=targets[index % len(targets)]) if len(targets) > 1 else None
        observation, info = env.reset(seed=seed+index, options=options)
        total = 0.
        for _ in range(env.horizon):
            action = np.zeros(env.action_space.shape, dtype=np.float32) if policy is None else policy.predict(
                observation, deterministic=True)[0]
            observation, reward, terminated, truncated, info = env.step(action)
            total += reward
            if viewer is not None:
                viewer.sync()
            if terminated or truncated:
                break
        records.append(dict(seed=seed+index, return_value=total, **info))
    return dict(episodes=episodes, success_rate=sum(r['success'] for r in records)/episodes,
                grasp_rate=(None if any(r['grasp'] is None for r in records) else
                            sum(r['grasp'] for r in records)/episodes),
                placement_rate=sum(r['placement'] for r in records)/episodes,
                failure_rate=sum(not r['success'] for r in records)/episodes,
                records=records)


class RecordEpisodes(BaseCallback):
    def __init__(self, output, every, viewer=None):
        super().__init__()
        self.output, self.every, self.viewer = output, every, viewer
        self.next_save = every
        self.completed = []

    def _on_step(self):
        if self.viewer is not None:
            self.viewer.sync()
        for done, info in zip(self.locals['dones'], self.locals['infos']):
            if done:
                record = {key: info.get(key) for key in (
                    'success', 'failure', 'grasp', 'placement', 'collisions', 'phase',
                    'visual_state', 'visual_confirmed', 'target', 'wrist_command_rad', 'wrist_travel_rad', 'neighbor_change', 'episode_steps', 'episode_wall_s', 'episode_reward_components')}
                record['training_step'] = self.num_timesteps
                self.completed.append(record)
                with (self.output/'episodes.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(record)+'\n')
        if self.num_timesteps >= self.next_save:
            self.model.save(self.output/f'checkpoint-{self.num_timesteps}')
            self.next_save = self.num_timesteps+self.every
        return True


def provenance(env):
    cfg = env.config
    paths = [Path(cfg['vision_library']), Path(cfg['motion_library']), Path(cfg['layout'])]
    paths += [p for p in sorted(Path(cfg['bundle']).rglob('*')) if p.is_file()]
    # Include native dependencies and environment/reward/observation sources.
    paths += list(Path(cfg['vision_library']).parent.glob('*.dll'))
    package = Path(__file__).resolve().parents[2]/'src/atom_mujoco'
    paths += [package/name for name in (
        'camera_manipulation_env.py', 'camera_reward.py', 'camera_policy.py',
        'native_vision.py', 'native_motion.py', 'visual_verification.py',
        'collision.py', 'motion_controller.py', 'backend.py', 'camera_only_env.py', 'neighbor_vision.py')]
    paths += [Path(__file__)]
    record = dict(environment_version=env.VERSION, configuration=cfg,
                  files={str(path.resolve()): sha(path) for path in sorted(set(paths))},
                  geometry=env.motion.geometry.tolist(), nominal_world_poses=env.poses.tolist(),
                  gripper_openings=env.openings.tolist(), residual_bounds=env.residual_bounds.tolist(),
                  runtime=dict(torch=torch.__version__, numpy=np.__version__))
    record['signature'] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=None, help='Fresh run directory; defaults to training/camera-manipulation/runs')
    parser.add_argument('--mode', choices=['smoke', 'train', 'evaluate', 'baseline'], default='smoke')
    parser.add_argument('--steps', type=int, default=128)
    parser.add_argument('--episodes', type=int, default=1)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--device', choices=['cpu', 'cuda', 'auto'], default='cpu')
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--resume', type=Path, help='Prior run directory, verified before continuing')
    parser.add_argument('--warm-start', type=Path, help='Prior run supplying policy weights; resets optimizer')
    parser.add_argument('--checkpoint-every', type=int, default=10000)
    parser.add_argument('--camera-only', action='store_true', help='Use RGB-only task reward and termination')
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    args.output = args.output or new_run('training/camera-manipulation/runs')
    if min(args.steps, args.episodes, args.checkpoint_every) <= 0:
        parser.error('Positive step and episode counts required')
    if args.warm_start and (args.mode != 'train' or args.resume or args.checkpoint):
        parser.error('Warm start requires train mode and excludes resume/checkpoint')
    if args.mode == 'evaluate' and not args.checkpoint:
        parser.error('Evaluation requires --checkpoint')
    if args.resume and (args.mode != 'train' or args.checkpoint):
        parser.error('Resume requires train mode and no separate checkpoint')
    if args.device == 'cuda' and not torch.cuda.is_available():
        parser.error('CUDA is unavailable in this PyTorch installation')
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    env = None
    viewer = None
    try:
        if args.camera_only:
            from atom_mujoco.camera_only_env import CameraOnlyEnv
            env = CameraOnlyEnv(args.config)
        else:
            env = CameraManipulationEnv(args.config)
        identity = provenance(env)
        if args.resume:
            previous = json.loads((args.resume/'run.json').read_text(encoding='utf-8'))
            previous_report = json.loads((args.resume/'report.json').read_text(encoding='utf-8'))
            if (previous['environment']['signature'] != identity['signature'] or
                    sha(args.resume/'policy.zip') != previous_report['checkpoint_sha256']):
                raise ValueError('Resume environment or checkpoint differs from recorded provenance')
        transfer = None
        if args.warm_start:
            source = args.warm_start.resolve(strict=True)
            previous_report = json.loads((source/'report.json').read_text(encoding='utf-8'))
            checkpoint_hash = sha(source/'policy.zip')
            if checkpoint_hash != previous_report['checkpoint_sha256']:
                raise ValueError('Warm-start checkpoint integrity mismatch')
            transfer = dict(source=str(source), checkpoint_sha256=checkpoint_hash,
                            scope='policy weights; fresh optimizer and step counter')
        run = dict(mode=args.mode, seed=args.seed, requested_steps=args.steps,
                   episodes=args.episodes, environment=identity,
                   resume=str(args.resume) if args.resume else None, warm_start=transfer,
                   actor='PPO MultiInputPolicy, P037 RGB/task/commands plus perception-valid mask',
                   reward='rgb_only' if args.camera_only else 'simulation_oracle')
        (args.output/'run.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
        if args.watch:
            import mujoco.viewer
            viewer = mujoco.viewer.launch_passive(env.sim.model, env.sim.data)
        started = time.perf_counter()
        baseline = evaluate(env, None, args.episodes, 100000+args.seed, viewer)
        report = dict(baseline=baseline, trained_steps=0)
        if args.camera_only:
            from PIL import Image
            frame = env.last_camera_frame
            Image.fromarray(frame.raw_rgb).save(args.output/'camera-final.png')
            Image.fromarray(frame.rectified_rgb).save(args.output/'homography-final.png')
        if args.mode in ('smoke', 'train'):
            check_env(env, warn=True, skip_render_check=True)
            policy = PPO.load(args.resume/'policy.zip', env=env, device=args.device) if args.resume else PPO(
                'MultiInputPolicy', env, n_steps=32, batch_size=32, n_epochs=2,
                learning_rate=3e-4, seed=args.seed, device=args.device, verbose=1)
            if args.warm_start:
                source_policy = PPO.load(args.warm_start/'policy.zip', device=args.device)
                if (source_policy.observation_space != env.observation_space
                        or source_policy.action_space != env.action_space):
                    raise ValueError('Warm-start policy spaces differ')
                policy.policy.load_state_dict(source_policy.policy.state_dict())
            before = weights_sha(policy)
            steps_before = policy.num_timesteps
            callback = RecordEpisodes(args.output, args.checkpoint_every, viewer)
            policy.learn(total_timesteps=args.steps, callback=callback,
                         reset_num_timesteps=not bool(args.resume))
            policy.save(args.output/'policy.zip')
            report.update(trained_steps=policy.num_timesteps-steps_before,
                          total_policy_steps=policy.num_timesteps,
                          weights_before=before, weights_after=weights_sha(policy),
                          training_episodes=callback.completed,
                          checkpoint_sha256=sha(args.output/'policy.zip'))
            # Load a new actor instance and evaluate without an optimizer step.
            loaded = PPO.load(args.output/'policy.zip', device=args.device)
            report['residual'] = evaluate(env, loaded, args.episodes, 100000+args.seed, viewer)
            report['checkpoint_reload_verified'] = weights_sha(loaded) == weights_sha(policy)
        elif args.mode == 'evaluate':
            loaded = PPO.load(args.checkpoint, device=args.device)
            if loaded.observation_space != env.observation_space or loaded.action_space != env.action_space:
                raise ValueError('Checkpoint observation/action schema mismatch')
            report['checkpoint_sha256'] = sha(args.checkpoint)
            report['residual'] = evaluate(env, loaded, args.episodes, 100000+args.seed, viewer)
        report['wall_time_s'] = time.perf_counter()-started
        report['status'] = 'completed'
        report['interpretation'] = 'Cycle execution evidence. Physical and visual qualification remain experimental.'
        (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    except Exception as exception:
        (args.output/'failure.json').write_text(json.dumps(dict(error=repr(exception)), indent=2),
                                              encoding='utf-8')
        raise
    finally:
        if viewer is not None:
            viewer.close()
        if env is not None:
            env.close()


if __name__ == '__main__':
    main()
