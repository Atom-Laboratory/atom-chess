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
    args = parser.parse_args()
    if args.steps<=0 or args.eval_episodes<=0 or args.horizon<=0:
        parser.error('Positive steps, horizon and evaluation episodes required')
    if args.output.exists():
        parser.error('Use a new output directory')
    if args.device=='cuda' and not torch.cuda.is_available():
        parser.error('This PyTorch environment has no CUDA device')
    args.output.mkdir(parents=True)
    torch.set_num_threads(2)
    started = time.perf_counter()
    env = VisualGraspEnv(args.bundle, horizon=args.horizon)
    try:
        check_env(env, warn=True)
        policy = PPO('CnnPolicy',env,n_steps=128,batch_size=32,n_epochs=4,
                     learning_rate=3e-4,seed=args.seed,device=args.device,verbose=1)
        initial = {key:value.clone() for key,value in policy.policy.state_dict().items()}
        policy.learn(total_timesteps=args.steps)
        policy.save(args.output/'policy')
        changed = any(not torch.equal(value,policy.policy.state_dict()[key]) for key,value in initial.items())
        seeds = list(range(10000,10000+args.eval_episodes))
        learned = evaluate(env,policy,seeds)
        hold = evaluate(env,None,seeds)
        loaded = PPO.load(args.output/'policy.zip',device=args.device)
        obs,_ = env.reset(seed=seeds[0])
        a,_ = policy.predict(obs,deterministic=True)
        b,_ = loaded.predict(obs,deterministic=True)
        assert np.allclose(a,b), 'Checkpoint reload changed deterministic action'
        report = dict(schema=1, algorithm='PPO', observation='96x96 RGB only',
            task='local E2 pawn grasp and lift', reward_source='simulation_oracle',
            model_parameters_updated=changed, trained_steps=policy.num_timesteps,
            cuda_available=torch.cuda.is_available(), device=str(policy.device),
            torch_version=torch.__version__, seed=args.seed,
            wall_time_s=time.perf_counter()-started,
            model_sha256=hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest(),
            checkpoint_sha256=hashlib.sha256((args.output/'policy.zip').read_bytes()).hexdigest(),
            evaluation=learned, hold_baseline=hold,
            success_rate=float(np.mean([x['success'] for x in learned])),
            validated_for_playground=False)
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        env.close()


if __name__=='__main__':
    main()
