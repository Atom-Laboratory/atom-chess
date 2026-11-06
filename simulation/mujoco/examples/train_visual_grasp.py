"""Train and evaluate an experimental pixel-only PPO grasp policy."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import BaseCallback
from atom_mujoco.training_monitor import RunRecorder, TrainingDisplay

from atom_mujoco.visual_grasp_env import VisualGraspEnv


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
    parser.add_argument('--resume',type=Path,help='Previous run directory; new output is required')
    args = parser.parse_args()
    if args.steps<=0 or args.eval_episodes<=0 or args.horizon<=0 or not np.isfinite(args.speed) or args.speed<=0:
        parser.error('Positive steps, horizon and evaluation episodes required')
    if args.output.exists():
        parser.error('Use a new output directory')
    if args.device=='cuda' and not torch.cuda.is_available():
        parser.error('This PyTorch environment has no CUDA device')
    model_hash = hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest()
    config = dict(environment_version=VisualGraspEnv.VERSION, stage=args.stage,
                  horizon=args.horizon, model_sha256=model_hash)
    if args.resume:
        previous = json.loads((args.resume/'run.json').read_text())
        previous_report = json.loads((args.resume/'report.json').read_text())
        if hashlib.sha256((args.resume/'policy.zip').read_bytes()).hexdigest() != previous_report['checkpoint_sha256']:
            parser.error('Resume checkpoint differs from recorded result')
        if previous['environment'] != config:
            parser.error('Resume requires identical environment version, model, stage and horizon')
    args.output.mkdir(parents=True)
    (args.output/'run.json').write_text(json.dumps(dict(environment=config,
        requested_steps=args.steps, seed=args.seed, watch=args.watch,
        resume=str(args.resume) if args.resume else None),indent=2)+'\n')
    torch.set_num_threads(2)
    started = time.perf_counter()
    env = VisualGraspEnv(args.bundle, horizon=args.horizon, stage=args.stage)
    display = None
    recorder = RunRecorder(args.output)
    try:
        check_env(env, warn=True)
        policy = PPO('CnnPolicy',env,n_steps=128,batch_size=32,n_epochs=4,
                     learning_rate=3e-4,seed=args.seed,device=args.device,verbose=1)
        if args.resume:
            policy = PPO.load(args.resume/'policy.zip',env=env,device=args.device)
            policy.set_random_seed(args.seed)
        initial = {key:value.clone() for key,value in policy.policy.state_dict().items()}
        if args.watch:
            env.reset(seed=args.seed)
            display = TrainingDisplay(env,speed=args.speed,device=str(policy.device))
            env.on_transition = display.update
        class Progress(BaseCallback):
            stopped = False

            def _on_step(self):
                recorder.step(self.num_timesteps,self.locals['rewards'][0],
                              self.locals['dones'][0],self.locals['infos'][0])
                if display:
                    display.step = self.num_timesteps
                    display.episodes = recorder.episodes
                    display.successes = recorder.successes
                    display.pump()
                if self.num_timesteps % 2048 == 0:
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
        report = dict(schema=2, environment=config, interrupted=interrupted, algorithm='PPO', observation='96x96 RGB only',
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
        env.close()


if __name__=='__main__':
    main()
