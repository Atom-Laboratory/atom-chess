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
from run_progress import RunProgress
from telemetry import TrainingCsv


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def weights_sha(policy):
    digest = hashlib.sha256()
    for name, tensor in sorted(policy.policy.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def evaluate(env, policy, episodes, seed, viewer=None, *, progress=None, stage='Evaluating policy'):
    records = []
    if progress is not None:
        progress.stage(stage, total=episodes, unit='episodes')
    for index in range(episodes):
        targets = getattr(env, 'targets', [])
        options = dict(target=targets[index % len(targets)]) if len(targets) > 1 else None
        observation, info = env.reset(seed=seed+index, options=options)
        total = 0.
        for step in range(1, env.horizon+1):
            action = np.zeros(env.action_space.shape, dtype=np.float32) if policy is None else policy.predict(
                observation, deterministic=True)[0]
            observation, reward, terminated, truncated, info = env.step(action)
            total += reward
            if viewer is not None:
                viewer.sync()
            if progress is not None:
                phase = info.get('phase') or 'running'
                progress.advance(index, f'Episode {index+1}/{episodes} | step {step}/{env.horizon} | {phase}')
            if terminated or truncated:
                break
        records.append(dict(seed=seed+index, return_value=total, **info))
        if progress is not None:
            outcome = 'passed' if info['success'] else (info.get('failure') or 'did not pass')
            progress.advance(index+1, f'Episode {index+1}: {outcome}', force=True)
    return dict(episodes=episodes, success_rate=sum(r['success'] for r in records)/episodes,
                grasp_rate=(None if any(r['grasp'] is None for r in records) else
                            sum(r['grasp'] for r in records)/episodes),
                placement_rate=sum(r['placement'] for r in records)/episodes,
                failure_rate=sum(not r['success'] for r in records)/episodes,
                records=records)


class RecordEpisodes(BaseCallback):
    def __init__(self, output, every, viewer=None, dashboard=None, *, progress, requested_steps):
        super().__init__()
        self.output, self.every, self.viewer = output, every, viewer
        self.dashboard = dashboard
        self.progress = progress
        self.requested_steps = requested_steps
        self.next_save = every
        self.completed = []

    def _on_training_start(self):
        self.csv = TrainingCsv(self.output, self.model.policy)
        self.training_start = time.perf_counter()
        self.training_start_step = self.model.num_timesteps
        rollout = self.model.n_steps*self.model.n_envs
        total = ((self.requested_steps+rollout-1)//rollout)*rollout
        detail = (f'Requested {self.requested_steps}; rounded to full PPO rollouts'
                  if total != self.requested_steps else None)
        self.progress.stage('Training PPO', total=total, unit='steps', detail=detail)

    def _on_rollout_start(self):
        self.record_update()

    def _on_training_end(self):
        self.record_update()
        self.progress.advance(self.num_timesteps-self.training_start_step,
                              'Final PPO update finished', force=True)

    def record_update(self):
        metrics = dict(self.logger.name_to_value)
        elapsed = time.perf_counter()-self.training_start
        metrics['time/fps'] = (self.num_timesteps-self.training_start_step)/max(elapsed, 1e-9)
        if self.model.ep_info_buffer:
            metrics['rollout/ep_rew_mean'] = float(np.mean([item['r'] for item in self.model.ep_info_buffer]))
            metrics['rollout/ep_len_mean'] = float(np.mean([item['l'] for item in self.model.ep_info_buffer]))
        if self.csv.record_update(self.num_timesteps, metrics) and self.dashboard is not None:
            self.dashboard.optimization(self.num_timesteps, metrics)

    def _on_step(self):
        if self.viewer is not None:
            self.viewer.sync()
        self.csv.record_step(self.num_timesteps, float(self.locals['rewards'][0]),
                             self.locals['dones'][0], self.locals['clipped_actions'][0],
                             self.locals['infos'][0])
        if self.dashboard is not None:
            self.dashboard.update(self.num_timesteps, float(self.locals['rewards'][0]),
                                  self.locals['infos'][0])
        step = self.num_timesteps-self.training_start_step
        info = self.locals['infos'][0]
        self.progress.advance(step, info.get('phase'))
        for done, info in zip(self.locals['dones'], self.locals['infos']):
            if done:
                record = {key: info.get(key) for key in (
                    'success', 'failure', 'grasp', 'placement', 'collisions', 'phase',
                    'visual_state', 'visual_confirmed', 'target', 'wrist_command_rad', 'wrist_travel_rad', 'neighbor_change', 'appearance_iou', 'forbidden_contact', 'contact_steps', 'topple_event', 'observed_offsets_m', 'neighbor_displacements_mm', 'episode_steps', 'episode_wall_s', 'episode_reward_components')}
                record['training_step'] = self.num_timesteps
                self.completed.append(record)
                with (self.output/'episodes.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(record)+'\n')
        if self.num_timesteps >= self.next_save:
            name = f'checkpoint-{self.num_timesteps}'
            self.progress.advance(step, f'Saving {name}.zip', force=True)
            self.model.save(self.output/name)
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
        'collision.py', 'motion_controller.py', 'backend.py', 'camera_only_env.py', 'neighbor_vision.py', 'piece_vision.py', 'contact_supervision.py')]
    if cfg.get('localize_source_rgb'):
        paths.extend([package/'board_piece_localization.py', package/'chess_commands.py'])
    paths += [Path(__file__)]
    record = dict(environment_version=env.VERSION, configuration=cfg,
                  files={str(path.resolve()): sha(path) for path in sorted(set(paths))},
                  geometry=env.motion.geometry.tolist(), nominal_world_poses=env.poses.tolist(),
                  gripper_openings=env.openings.tolist(), residual_bounds=env.residual_bounds.tolist(),
                  runtime=dict(torch=torch.__version__, numpy=np.__version__))
    record['signature'] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    return record


def same_environment(previous, current):
    if previous['signature'] == current['signature']:
        return True
    # These launcher revisions differ only in instrumentation for exact resume.
    launcher = str(Path(__file__).resolve())
    old_hash = previous['files'].get(launcher)
    if old_hash not in {
        '6542e9045cc4b58096426d8b242fe86c6e4aa2e53452a044997e828e969aaad8',
        '4b1170a294838d7346e520099d50ab3b39fafe2900f73f272fb0301a1cdb30e8',
        '59da3952d5bd0a2040c88db30ecad6c765ea9deddd5a433f0078c9d67a478455',
        '609af6ed96eaf48b06b3daa68a83474086d6af59dd9c097cb480bb84b9e14644',
    }:
        return False
    candidate = dict(current, files=dict(current['files'], **{launcher: old_hash}))
    candidate.pop('signature')
    return hashlib.sha256(json.dumps(candidate, sort_keys=True).encode()).hexdigest() == previous['signature']


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
    warm = parser.add_mutually_exclusive_group()
    warm.add_argument('--warm-start', type=Path, help='Prior run supplying policy weights; resets optimizer')
    warm.add_argument('--warm-start-checkpoint', type=Path, help='Intermediate PPO archive in a prior run')
    parser.add_argument('--checkpoint-sha256', help='Expected archive SHA-256 for --warm-start-checkpoint')
    parser.add_argument('--checkpoint-every', type=int, default=10000)
    parser.add_argument('--camera-only', action='store_true', help='Use RGB task evidence with optional simulated contact and toppling supervision')
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--dashboard', action='store_true', help='Live PPO graph, losses and reward components (train/smoke)')
    args = parser.parse_args()
    args.output = args.output or new_run('training/camera-manipulation/runs')
    if args.dashboard and args.mode not in ('train', 'smoke'):
        parser.error('--dashboard requires train or smoke mode')
    if min(args.steps, args.episodes, args.checkpoint_every) <= 0:
        parser.error('Positive step and episode counts required')
    if (args.warm_start or args.warm_start_checkpoint) and (args.mode != 'train' or args.resume or args.checkpoint):
        parser.error('Warm start requires train mode and excludes resume/checkpoint')
    if args.checkpoint_sha256 and not args.warm_start_checkpoint:
        parser.error('--checkpoint-sha256 requires --warm-start-checkpoint')
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
    dashboard = None
    callback = None
    progress = RunProgress()
    try:
        if args.dashboard:
            from dashboard_publisher import DashboardPublisher
            dashboard = DashboardPublisher(args.output)
            progress.dashboard = dashboard
        progress.stage('Loading environment and checking run files')
        if args.camera_only:
            from atom_mujoco.camera_only_env import CameraOnlyEnv
            env = CameraOnlyEnv(args.config)
        else:
            env = CameraManipulationEnv(args.config)
        identity = provenance(env)
        if args.resume:
            previous = json.loads((args.resume/'run.json').read_text(encoding='utf-8'))
            previous_report = json.loads((args.resume/'report.json').read_text(encoding='utf-8'))
            if (not same_environment(previous['environment'], identity) or
                    sha(args.resume/'policy.zip') != previous_report['checkpoint_sha256']):
                raise ValueError('Resume environment or checkpoint differs from recorded provenance')
        transfer = None
        source_policy = None
        if args.warm_start or args.warm_start_checkpoint:
            archive = (args.warm_start_checkpoint or args.warm_start/'policy.zip').resolve(strict=True)
            source = archive.parent
            donor = json.loads((source/'run.json').read_text(encoding='utf-8'))
            expected = args.checkpoint_sha256
            if args.warm_start:
                expected = json.loads((source/'report.json').read_text(encoding='utf-8'))['checkpoint_sha256']
            checkpoint_hash = sha(archive)
            if expected and checkpoint_hash != expected.lower():
                raise ValueError('Warm-start checkpoint integrity mismatch')
            source_policy = PPO.load(archive, device=args.device)
            if (source_policy.observation_space != env.observation_space
                    or source_policy.action_space != env.action_space):
                raise ValueError('Warm-start policy spaces differ')
            transfer = dict(source=str(source), checkpoint=str(archive), checkpoint_sha256=checkpoint_hash,
                            source_steps=source_policy.num_timesteps, weights_sha256=weights_sha(source_policy),
                            source_environment=donor['environment']['signature'],
                            scope='policy weights; fresh optimizer and step counter')
        run = dict(mode=args.mode, seed=args.seed, requested_steps=args.steps,
                   episodes=args.episodes, environment=identity,
                   resume=str(args.resume) if args.resume else None, warm_start=transfer,
                   actor='PPO MultiInputPolicy, P037 RGB/task/commands plus perception-valid mask',
                   reward=getattr(env, 'reward_source', 'simulation_oracle'))
        (args.output/'run.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
        if args.watch:
            progress.stage('Opening MuJoCo viewer')
            import mujoco.viewer
            viewer = mujoco.viewer.launch_passive(env.sim.model, env.sim.data)
        started = time.perf_counter()
        baseline = evaluate(env, None, args.episodes, 100000+args.seed, viewer,
                            progress=progress, stage='Evaluating baseline')
        report = dict(baseline=baseline, trained_steps=0)
        if args.camera_only:
            from PIL import Image
            frame = env.last_camera_frame
            Image.fromarray(frame.raw_rgb).save(args.output/'camera-final.png')
            Image.fromarray(frame.rectified_rgb).save(args.output/'homography-final.png')
        if args.mode in ('smoke', 'train'):
            progress.stage('Checking the Gym environment and preparing PPO')
            check_env(env, warn=True, skip_render_check=True)
            policy = PPO.load(args.resume/'policy.zip', env=env, device=args.device) if args.resume else PPO(
                'MultiInputPolicy', env, n_steps=32, batch_size=32, n_epochs=2,
                learning_rate=3e-4, seed=args.seed, device=args.device, verbose=1)
            if source_policy is not None:
                policy.policy.load_state_dict(source_policy.policy.state_dict())
                if weights_sha(policy) != transfer['weights_sha256']:
                    raise RuntimeError('Warm-start weights failed verification')
            before = weights_sha(policy)
            steps_before = policy.num_timesteps
            if dashboard is not None:
                dashboard.attach(policy.policy)
            callback = RecordEpisodes(args.output, args.checkpoint_every, viewer, dashboard,
                                      progress=progress, requested_steps=args.steps)
            policy.learn(total_timesteps=args.steps, callback=callback,
                         reset_num_timesteps=not bool(args.resume))
            progress.stage('Saving final policy')
            policy.save(args.output/'policy.zip')
            report.update(trained_steps=policy.num_timesteps-steps_before,
                          total_policy_steps=policy.num_timesteps,
                          weights_before=before, weights_after=weights_sha(policy),
                          training_episodes=callback.completed,
                          checkpoint_sha256=sha(args.output/'policy.zip'))
            # Load a new actor instance and evaluate without an optimizer step.
            loaded = PPO.load(args.output/'policy.zip', device=args.device)
            report['residual'] = evaluate(env, loaded, args.episodes, 100000+args.seed, viewer,
                                          progress=progress, stage='Evaluating saved policy')
            report['checkpoint_reload_verified'] = weights_sha(loaded) == weights_sha(policy)
        elif args.mode == 'evaluate':
            progress.stage('Loading policy for evaluation')
            loaded = PPO.load(args.checkpoint, device=args.device)
            if loaded.observation_space != env.observation_space or loaded.action_space != env.action_space:
                raise ValueError('Checkpoint observation/action schema mismatch')
            report['checkpoint_sha256'] = sha(args.checkpoint)
            report['residual'] = evaluate(env, loaded, args.episodes, 100000+args.seed, viewer,
                                          progress=progress)
        report['wall_time_s'] = time.perf_counter()-started
        report['status'] = 'completed'
        report['interpretation'] = 'Cycle execution evidence. Physical and visual qualification remain experimental.'
        (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
        progress.stage('Run complete', detail=str(args.output/'report.json'))
    except KeyboardInterrupt:
        progress.stage('Run interrupted', detail=str(args.output))
        raise
    except Exception as exception:
        progress.stage('Run failed', detail=str(exception))
        (args.output/'failure.json').write_text(json.dumps(dict(error=repr(exception)), indent=2),
                                              encoding='utf-8')
        raise
    finally:
        if callback is not None and hasattr(callback, 'csv'):
            callback.csv.close()
        if dashboard is not None:
            dashboard.close()
        if viewer is not None:
            viewer.close()
        if env is not None:
            env.close()


if __name__ == '__main__':
    main()
