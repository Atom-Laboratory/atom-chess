"""Short autonomous temporal-control PPO experiments, isolated from P038 residuals."""
import argparse
from collections import Counter
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from atom_mujoco.autonomous_env import AutonomousManipulationEnv
from atom_mujoco.autonomous_policy import AutonomousFeatures, POLICY_VERSION
from atom_mujoco.paths import new_run

SUPPORT = Path(__file__).resolve().parents[1]/'camera-manipulation'
sys.path.insert(0, str(SUPPORT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from telemetry import TrainingCsv
from run_progress import RunProgress
from resources import sample_hardware


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def weights_sha(policy):
    digest = hashlib.sha256()
    for name, tensor in sorted(policy.policy.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


class TimedPPO(PPO):
    """Measure optimizer wall time without changing the update."""

    def train(self):
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        started = time.perf_counter()
        super().train()
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        self.optimizer_wall_s = getattr(self, 'optimizer_wall_s', 0.) + time.perf_counter()-started


def save_checkpoint(model, path):
    temporary = path.with_name(path.stem+'-writing.zip')
    model.save(temporary)
    temporary.replace(path)
    digest = sha(path)
    path.with_suffix('.sha256').write_text(digest+'\n', encoding='ascii')
    return digest


class Recorder(BaseCallback):
    def __init__(self, env, output, progress, checkpoint_every, watch=None, dashboard=None):
        super().__init__()
        self.scene, self.output, self.progress = env, output, progress
        self.checkpoint_every, self.watch = checkpoint_every, watch
        self.dashboard = dashboard
        self.started = time.perf_counter()
        self.completed = []
        self.validations = Counter()
        self.coverage = Counter()
        self.next_checkpoint = checkpoint_every
        self.episode = 1
        self.stream = (output/'decisions.jsonl').open('x', encoding='utf-8', buffering=1)
        self.performance_stream = (output/'performance.csv').open('x', newline='', encoding='utf-8', buffering=1)
        self.performance = csv.DictWriter(self.performance_stream, fieldnames=(
            'step', 'episode', 'validation', 'pad_distance_m', 'best_pad_distance_m',
            'reach_threshold_m', 'validation_s', 'physics_s', 'perception_s', 'feedback_s', 'total_s'))
        self.performance.writeheader()
        self.hardware_stream = (output/'hardware.jsonl').open('x', encoding='utf-8', buffering=1)

    def _on_training_start(self):
        self.csv = TrainingCsv(self.output, self.model.policy)
        if self.watch:
            self.watch.stage = 'TRAINING'
        self.progress.stage('Autonomous PPO', total=self.locals['total_timesteps'], unit='decisions')

    def _on_rollout_start(self):
        self.record_update()

    def _on_training_end(self):
        self.record_update()
        self.progress.advance(self.num_timesteps, 'Optimizer finished', force=True)

    def record_update(self):
        if self.csv.record_update(self.num_timesteps, self.logger.name_to_value):
            hardware = sample_hardware(self.model.device.type)
            self.hardware_stream.write(json.dumps(hardware)+'\n')
            if self.dashboard:
                self.dashboard.optimization(self.num_timesteps, self.logger.name_to_value)
                self.dashboard.write(hardware=hardware)

    def _on_step(self):
        info = dict(self.locals['infos'][0])
        info.pop('terminal_observation', None)
        action = self.locals['clipped_actions'][0]
        done = bool(self.locals['dones'][0])
        self.csv.record_step(self.num_timesteps, float(self.locals['rewards'][0]), done, action, info)
        timing = info.get('timings_s', {})
        self.performance.writerow(dict(step=self.num_timesteps, episode=self.episode,
            validation=info['validation']['status'],
            **{name: info.get(name) for name in ('pad_distance_m', 'best_pad_distance_m', 'reach_threshold_m')},
            **{name+'_s': timing.get(name) for name in ('validation', 'physics', 'perception', 'feedback', 'total')}))
        if self.dashboard:
            self.dashboard.update(self.num_timesteps, float(self.locals['rewards'][0]), info)
        self.validations[info['validation']['status']] += 1
        choice = info['choice']
        pitch = self.scene.base.sim.manifest['scene']['square_size_m']
        # Bins have physical interpretations and do not count numerical jitter
        # as a new strategy. They describe requests; accepted bins are separate.
        signature = (*np.floor(np.asarray(choice['xyz_m'])/pitch).astype(int).tolist(),
                     int(choice['wrist_rad']/(np.pi/4)), bool(choice['elbow_down']))
        self.coverage[(str(signature), info['validation']['status'] == 'ACCEPTED')] += 1
        self.stream.write(json.dumps(dict(info, training_step=self.num_timesteps,
                                          episode_index=self.episode, action=action.tolist()))+'\n')
        if self.watch:
            self.watch.step = self.num_timesteps
            self.watch.total = self.locals['total_timesteps']
        if done:
            self.completed.append(dict(training_step=self.num_timesteps, **info))
            self.episode += 1
            if self.watch:
                self.watch.trail = []
                self.watch.episode = self.episode
        self.progress.advance(self.num_timesteps,
                              f'{info["validation"]["status"]} | episode {self.episode} | '
                              f'gap {1000*info.get("pad_distance_m", 0):.1f} mm | '
                              f'best {1000*info.get("best_pad_distance_m", 0):.1f} mm | '
                              f'return {info.get("episode_return", 0):.2f}')
        if self.num_timesteps >= self.next_checkpoint:
            save_checkpoint(self.model, self.output/f'checkpoint-{self.num_timesteps}.zip')
            if self.dashboard:
                self.dashboard.write(experiment=dict(run=self.output.name, piece=self.scene.base.config['piece'],
                    objective=self.scene.objective, device=self.model.device.type,
                    checkpoint=f'checkpoint-{self.num_timesteps}.zip'))
            self.next_checkpoint += self.checkpoint_every
        return True

    def close(self):
        self.stream.close()
        self.performance_stream.close()
        self.hardware_stream.close()
        if hasattr(self, 'csv'):
            self.csv.close()


def evaluate(env, policy, seeds, stochastic, progress, watch, dashboard=None, *, stage='EVALUATION'):
    records = []
    progress.stage('Evaluating autonomous policy', total=len(seeds), unit='episodes')
    if watch:
        watch.stage = stage
    for index, seed in enumerate(seeds):
        observation, _ = env.reset(seed=seed)
        if watch:
            watch.episode = index+1
            watch.trail = []
        for _ in range(env.horizon):
            action = policy.predict(observation, deterministic=not stochastic)[0]
            observation, reward, terminated, truncated, info = env.step(action)
            if dashboard:
                dashboard.update(env.steps, reward, info)
            if terminated or truncated:
                break
        records.append(dict(seed=seed, **info))
        progress.advance(index+1, f'{info["failure"] or "SUCCESS"} | best gap '
                         f'{1000*info["best_pad_distance_m"]:.1f} mm', force=True)
    return dict(episodes=len(records), seeds=seeds, stochastic=stochastic,
                success_rate=sum(info['success'] for info in records)/len(records),
                median_best_distance_m=float(np.median([r['best_pad_distance_m'] for r in records])),
                records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--steps', type=int, default=32)
    parser.add_argument('--episodes', type=int, default=2)
    parser.add_argument('--horizon', type=int, default=128)
    parser.add_argument('--objective', choices=AutonomousManipulationEnv.OBJECTIVES, default='lift')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--evaluation-seed', type=int, default=910000)
    parser.add_argument('--checkpoint-every', type=int, default=512)
    parser.add_argument('--rollout-steps', type=int, default=32)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--learning-rate', type=float, default=3e-4)
    parser.add_argument('--ent-coef', type=float, default=0.)
    parser.add_argument('--target-kl', type=float, default=.03)
    parser.add_argument('--dashboard', action='store_true', help='Live actual PPO graph, loss and reward')
    parser.add_argument('--evaluate-before', action='store_true', help='Evaluate initial weights on the same seeds')
    parser.add_argument('--evaluate-only', action='store_true', help='Evaluate verified weights without optimization')
    parser.add_argument('--warm-start', type=Path,
                        help='Completed autonomous run supplying weights with a fresh optimizer')
    parser.add_argument('--warm-start-checkpoint', type=Path,
                        help='Checkpoint with run.json and SHA-256 sidecar; fresh optimizer')
    parser.add_argument('--allow-config-transfer', action='store_true',
                        help='Explicitly transfer compatible weights to a different environment configuration')
    viewer = parser.add_mutually_exclusive_group()
    viewer.add_argument('--watch', action='store_true', help='Three-panel camera diagnostics')
    viewer.add_argument('--watch-native', action='store_true', help='Interactive MuJoCo 3D window')
    viewer.add_argument('--headless', action='store_true', help='Explicitly disable the default native Watch')
    parser.add_argument('--keep-watch-open', action='store_true',
                        help='Keep the native viewer open after saving the report')
    parser.add_argument('--show-colliders', action='store_true')
    parser.add_argument('--device', choices=('cpu', 'cuda', 'auto'), default='cuda',
                        help='PPO inference and optimizer device')
    parser.add_argument('--stochastic-evaluation', action='store_true')
    parser.add_argument('--torch-threads', type=int, default=2)
    args = parser.parse_args()
    if not args.watch and not args.watch_native and not args.headless:
        args.watch_native = True
    if args.watch_native:
        args.keep_watch_open = True
    if args.keep_watch_open and not args.watch_native:
        parser.error('--keep-watch-open requires --watch-native')
    if min(args.steps, args.episodes, args.horizon, args.checkpoint_every, args.rollout_steps,
           args.batch_size, args.epochs, args.torch_threads) <= 0 or args.rollout_steps < 2 or args.batch_size < 2:
        parser.error('Step, horizon, episode and checkpoint counts must be positive')
    if args.rollout_steps % args.batch_size:
        parser.error('--rollout-steps must be divisible by --batch-size')
    if not np.isfinite([args.learning_rate, args.ent_coef, args.target_kl]).all() or args.learning_rate <= 0 or args.ent_coef < 0 or args.target_kl <= 0:
        parser.error('Learning rate must be positive and entropy coefficient nonnegative')
    if args.warm_start and args.warm_start_checkpoint:
        parser.error('Choose a completed run or an intermediate checkpoint')
    if args.evaluate_only and not (args.warm_start or args.warm_start_checkpoint):
        parser.error('--evaluate-only requires verified source weights')
    if args.seed in range(args.evaluation_seed, args.evaluation_seed+args.episodes):
        parser.error('Evaluation seeds must exclude the training seed')
    if args.device in ('cuda', 'auto') and not torch.cuda.is_available():
        parser.error('CUDA is unavailable in this PyTorch installation')
    device = 'cuda' if args.device == 'auto' else args.device
    output = args.output or new_run('training/autonomous-manipulation/runs')
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(args.torch_threads)
    env = watch = recorder = model = dashboard = None
    progress = RunProgress()
    try:
        if args.dashboard:
            from dashboard_publisher import DashboardPublisher
            dashboard = DashboardPublisher(output)
            progress.dashboard = dashboard
        progress.stage('Preparing autonomous visual environment')
        env = AutonomousManipulationEnv(args.config, objective=args.objective, horizon=args.horizon)
        module = Path(__file__).resolve().parents[2]/'src/atom_mujoco'
        sources = sorted(module.glob('*.py'))+list(Path(__file__).parent.glob('*.py'))+[
                   SUPPORT/name for name in ('telemetry.py', 'run_progress.py', 'dashboard.py', 'dashboard_publisher.py')]
        cfg = env.base.config
        assets = sorted(p for p in Path(cfg['bundle']).rglob('*') if p.is_file())
        libraries = list(Path(cfg['vision_library']).parent.glob('*.dll'))+[Path(cfg['motion_library'])]
        run = dict(schema=1, environment_version=env.VERSION, policy_version=POLICY_VERSION, config=cfg, args={
                   key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
                   config_sha256=sha(args.config), policy_device=device,
                   policy_gpu=torch.cuda.get_device_name() if device == 'cuda' else None,
                   torch_version=torch.__version__, cuda_version=torch.version.cuda,
                   started_at_unix_s=time.time(),
                   files_sha256={str(path.resolve()): sha(path) for path in (*sources, *assets, *libraries)},
                   control_rates_si=env.control.rates.tolist(),
                   max_action_intervals=env.control.max_intervals,
                   action_schema=env.action_axes,
                   actor_inputs=list(env.observation_space.spaces),
                   reward_source='simulation_supervised_camera_actor',
                   initial_weights='fresh; previous residual checkpoint semantics differ')
        (output/'run.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
        env.reset(seed=args.seed)
        if args.watch or args.watch_native:
            from watch import NativeWatch, Watch
            watch = (NativeWatch(env, show_colliders=args.show_colliders) if args.watch_native
                     else Watch(env, output, show_colliders=args.show_colliders))
            env.observer = lambda info: watch.update(info, force=env.finished)
            watch.total = ((args.steps+args.rollout_steps-1)//args.rollout_steps)*args.rollout_steps
            watch.update(env.last_info, force=True)
        model = TimedPPO('MultiInputPolicy', env, n_steps=args.rollout_steps, batch_size=args.batch_size, n_epochs=args.epochs,
                    learning_rate=args.learning_rate, ent_coef=args.ent_coef,
                    target_kl=args.target_kl,
                    seed=args.seed, device=device, verbose=1,
                    policy_kwargs={'log_std_init': float(np.log(.4)),
                                   'features_extractor_class': AutonomousFeatures})
        if args.warm_start or args.warm_start_checkpoint:
            archive = args.warm_start_checkpoint or args.warm_start/'policy.zip'
            source_run = json.loads((archive.parent/'run.json').read_text(encoding='utf-8'))
            expected = (archive.with_suffix('.sha256').read_text(encoding='ascii').strip()
                        if args.warm_start_checkpoint else
                        json.loads((args.warm_start/'report.json').read_text(encoding='utf-8'))['checkpoint_sha256'])
            if source_run['environment_version'] != env.VERSION:
                raise ValueError('Warm-start action semantics differ')
            if source_run.get('policy_version', 1) != POLICY_VERSION:
                raise ValueError('Warm-start policy architecture differs. Use its original runner or train a fresh policy.')
            config_transfer = source_run.get('config_sha256') != run['config_sha256']
            if config_transfer and not args.allow_config_transfer:
                raise ValueError('Warm-start configuration differs. Use the original config or explicitly pass --allow-config-transfer.')
            if sha(archive) != expected:
                raise ValueError('Warm-start checkpoint identity differs')
            source = PPO.load(archive, device='cpu')
            if source.observation_space != env.observation_space or source.action_space != env.action_space:
                raise ValueError('Warm-start policy spaces differ')
            model.policy.load_state_dict(source.policy.state_dict())
            run['initial_weights'] = dict(source=str(archive.resolve()),
                                          config_transfer=config_transfer,
                                          source_config_sha256=source_run.get('config_sha256'),
                                          sha256=sha(archive), weights_sha256=weights_sha(source),
                                          scope='autonomous policy weights; fresh optimizer')
            (output/'run.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
        before = weights_sha(model)
        if dashboard:
            dashboard.attach(model.policy, action_description='continuous temporal controls')
            dashboard.write(experiment=dict(run=output.name, piece=cfg['piece'],
                            objective=args.objective, device=device, algorithm='PPO'),
                            hardware=sample_hardware(device), status='Preparing evaluation/training')
        seeds = list(range(args.evaluation_seed, args.evaluation_seed+args.episodes))
        baseline = (evaluate(env, model, seeds, args.stochastic_evaluation, progress, watch, dashboard,
                             stage='INITIAL EVALUATION')
                    if args.evaluate_before else None)
        if baseline is not None:
            (output/'baseline.json').write_text(json.dumps(baseline, indent=2), encoding='utf-8')
        training_wall_s = 0.
        if not args.evaluate_only:
            env.reset(seed=args.seed)
            recorder = Recorder(env, output, progress, args.checkpoint_every, watch, dashboard)
            started = time.perf_counter()
            model.learn(args.steps, callback=recorder)
            training_wall_s = time.perf_counter()-started
        optimizer_wall_s = getattr(model, 'optimizer_wall_s', 0.)
        after = weights_sha(model)
        progress.stage('Saving autonomous policy')
        save_checkpoint(model, output/'policy.zip')
        model = PPO.load(output/'policy.zip', device=device)
        if weights_sha(model) != after:
            raise RuntimeError('Reloaded policy weights differ')
        evaluation = evaluate(env, model, seeds, args.stochastic_evaluation, progress, watch, dashboard)
        from PIL import Image
        Image.fromarray(env.last_frame.raw_rgb).save(output/'camera-final.png')
        Image.fromarray(env.last_frame.rectified_rgb).save(output/'board-final.png')
        report = dict(status='completed', steps=recorder.num_timesteps if recorder else 0,
                      training_wall_s=training_wall_s, optimizer_wall_s=optimizer_wall_s,
                      checkpoint_sha256=sha(output/'policy.zip'), evaluation=evaluation,
                      weights_before=before, weights_after=after, checkpoint_reload_verified=True,
                      baseline=baseline,
                      training_episodes=recorder.completed if recorder else [],
                      validation_counts=dict(recorder.validations) if recorder else {},
                      requested_strategy_bins=len({key[0] for key in recorder.coverage}) if recorder else 0,
                      accepted_strategy_bins=len({key[0] for key in recorder.coverage if key[1]}) if recorder else 0,
                      diversity_bins=dict(xyz_m=env.sim.manifest['scene']['square_size_m'],
                                          wrist_rad=np.pi/4, elbow='binary'),
                      interpretation='Short interface experiment; task learning and generalization require qualification')
        (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        progress.stage('Autonomous run complete', detail=str(output/'report.json'))
        if dashboard:
            dashboard.write(status='Completed')
        print({key: value for key, value in report.items() if key not in ('evaluation', 'training_episodes')})
    except BaseException as error:
        progress.stage('Autonomous run stopped', detail=repr(error))
        recovery = None
        if model is not None:
            try:
                recovery = save_checkpoint(model, output/'interrupted-policy.zip')
            except Exception as save_error:
                recovery = dict(error=repr(save_error))
        (output/'failure.json').write_text(json.dumps(dict(error=repr(error),
            traceback=traceback.format_exc(), recovery=recovery,
            pending_action=getattr(env, 'pending_action', None),
            recovery_scope='weights only; use --warm-start-checkpoint with fresh optimizer')), encoding='utf-8')
        raise
    else:
        if args.keep_watch_open:
            print('[ATOM] Training and evaluation finished. Close MuJoCo to exit.', flush=True)
            try:
                watch.wait_until_closed()
            except KeyboardInterrupt:
                pass
    finally:
        if recorder:
            recorder.close()
        if watch:
            watch.close()
        if env:
            env.close()
        if dashboard:
            dashboard.close()


if __name__ == '__main__':
    main()
