"""Qualify a saved visual policy on fixed varied seeds with forbidden-contact checks."""
import argparse
import json
from pathlib import Path

from PIL import Image
from stable_baselines3 import PPO
import torch

from atom_mujoco.camera_only_env import CameraOnlyEnv
from run import provenance, same_environment, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=30)
    parser.add_argument('--start-seed', type=int, default=910000)
    parser.add_argument('--minimum-rate', type=float, default=.9)
    args = parser.parse_args()
    if args.episodes < 30 or not 0 < args.minimum_rate <= 1:
        parser.error('Use at least 30 episodes and a rate in (0,1]')
    torch.set_num_threads(2)
    args.output.mkdir(parents=True, exist_ok=False)
    env = CameraOnlyEnv(args.config)
    try:
        if not env.qualification or not env.contact_penalty or env.config.get('placement_jitter_m', 0) <= 0:
            raise ValueError('Qualification requires appearance, placement variation and contact supervision')
        training = json.loads((args.run/'run.json').read_text(encoding='utf-8'))
        report = json.loads((args.run/'report.json').read_text(encoding='utf-8'))
        if not same_environment(training['environment'], provenance(env)):
            raise ValueError('Environment differs from saved training provenance')
        checkpoint = args.run/'policy.zip'
        if sha(checkpoint) != report['checkpoint_sha256']:
            raise ValueError('Checkpoint integrity mismatch')
        model = PPO.load(checkpoint, device='cpu')
        if model.action_space != env.action_space or model.observation_space != env.observation_space:
            raise ValueError('Policy spaces differ')
        seeds = list(range(args.start_seed, args.start_seed+args.episodes))
        protocol = dict(seeds=seeds, minimum_rate=args.minimum_rate,
                        checkpoint_sha256=sha(checkpoint), configuration=env.config,
                        source_sha256=sha(Path(__file__)))
        (args.output/'protocol.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
        records = []
        for index, seed in enumerate(seeds):
            folder = args.output/f'episode-{index:02d}-seed-{seed}'
            folder.mkdir()
            observation, _ = env.reset(seed=seed)
            Image.fromarray(env.last_camera_frame.raw_rgb).save(folder/'before-rgb.png')
            Image.fromarray(env.last_camera_frame.rectified_rgb).save(folder/'before-board.png')
            for _ in range(env.horizon):
                action = model.predict(observation, deterministic=True)[0]
                observation, reward, done, truncated, info = env.step(action)
                if done or truncated:
                    break
            Image.fromarray(env.last_camera_frame.raw_rgb).save(folder/'after-rgb.png')
            Image.fromarray(env.last_camera_frame.rectified_rgb).save(folder/'after-board.png')
            approved = bool(info['success'] and info['topple_event'] is None
                            and info['appearance_iou'] is not None
                            and info['appearance_iou'] >= env.appearance.minimum_iou
                            and info['neighbor_change'] is not None
                            and all(x <= env.neighbors.limit for x in info['neighbor_change'].values()))
            record = dict(seed=seed, approved=approved, **info)
            (folder/'result.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
            records.append(record)
            result = dict(episodes=len(records), planned_episodes=len(seeds),
                          approved=sum(x['approved'] for x in records),
                          approval_rate=sum(x['approved'] for x in records)/len(records),
                          records=records)
            result['passed'] = len(records) == len(seeds) and result['approval_rate'] >= args.minimum_rate
            (args.output/'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"{index+1}/{len(seeds)} seed={seed} approved={approved} failure={info['failure']}", flush=True)
    finally:
        env.close()


if __name__ == '__main__':
    main()
