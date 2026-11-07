"""Reproducible rollouts, paired evaluation and portable policy artifacts."""

import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .environment import ReachEnv, conventional_action


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def rollout(env, policy, seed, *, options=None, trajectory=False):
    observation, info = env.reset(seed=seed, options=options)
    total_reward = smoothness = 0.0
    states = [env.controller.q.tolist()] if trajectory else None
    start = time.perf_counter()
    for _ in range(env.config['horizon']):
        if policy == 'conventional':
            action = conventional_action(env)
        elif policy == 'random':
            action = env.np_random.uniform(-1, 1, env.model.dof)
        else:
            action, _ = policy.predict(observation, deterministic=True)
        observation, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        smoothness += info['command_change_squared']
        if trajectory:
            states.append(env.controller.q.tolist())
        if terminated or truncated:
            break
    info.update(seed=int(seed), return_sum=total_reward,
                command_change_sum=smoothness, wall_time_s=time.perf_counter() - start)
    if trajectory:
        return info, {
            'schema': 'atom-kinematic-trajectory-v1',
            'profile': env.config['profile'], 'model_sha256': env.model.sha256,
            'joint_names': env.model.names, 'tip': env.model.tip,
            'dt': env.config['dt'], 'velocity_fraction': env.config['velocity_fraction'],
            'action_slew_per_step': env.config['action_slew_per_step'],
            'target_pose': env.target_pose.tolist(), 'goal_q': env.goal.tolist(),
            'positions': states,
            'tip_positions': [env.model.fk(q)[:3, 3].tolist() for q in states],
            'result': info,
        }
    return info


def summarize(rows):
    successes = sum(row['is_success'] for row in rows)
    n = len(rows)
    p = successes / n
    z = 1.96
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1+z*z/n)
    return {
        'episodes': n, 'successes': successes, 'success_rate': p,
        'success_rate_wilson95': [float(center-half), float(center+half)],
        'position_error_mean_m': float(np.mean([r['position_error_m'] for r in rows])),
        'position_error_max_m': max(r['position_error_m'] for r in rows),
        'orientation_error_mean_rad': float(np.mean([r['orientation_error_rad'] for r in rows])),
        'steps_mean': float(np.mean([r['steps'] for r in rows])),
        'simulated_time_mean_s': float(np.mean([r['simulated_time_s'] for r in rows])),
        'wall_time_total_s': sum(r['wall_time_s'] for r in rows),
        'return_mean': float(np.mean([r['return_sum'] for r in rows])),
        'command_change_mean': float(np.mean([r['command_change_sum'] for r in rows])),
        'limit_violations': sum(r['limit_violations'] for r in rows),
        'collisions': None, 'collision_detection': 'not_modeled',
        'timeouts': sum(r['status'] == 'timeout' for r in rows),
    }


def evaluate(config, policy, seeds):
    env = ReachEnv(config)
    try:
        rows = [rollout(env, policy, int(seed)) for seed in seeds]
        return {'summary': summarize(rows), 'episodes': rows}
    finally:
        env.close()


def export_actor(model, destination, config, model_hash):
    """Export deterministic SAC actor as non-executable NumPy arrays + metadata."""
    import torch
    arrays, layers = {}, []
    for layer in list(model.actor.latent_pi) + [model.actor.mu]:
        if isinstance(layer, torch.nn.Linear):
            index = len(layers)
            arrays[f'w{index}'] = layer.weight.detach().cpu().numpy()
            arrays[f'b{index}'] = layer.bias.detach().cpu().numpy()
            layers.append('linear')
        elif isinstance(layer, torch.nn.ReLU):
            layers.append('relu')
        else:
            raise ValueError(f'Unsupported actor layer {type(layer)}')
    arrays['metadata'] = np.array(json.dumps({
        'schema': 'atom-sac-actor-v1', 'layers': layers, 'model_sha256': model_hash,
        'config': {k: v for k, v in config.items() if k not in ('model', 'training')},
    }))
    np.savez_compressed(destination, **arrays)


class NumpyActor:
    """Inference-only actor; independent of PyTorch and the training process."""

    def __init__(self, path, config, model_hash):
        with np.load(path, allow_pickle=False) as data:
            self.metadata = json.loads(str(data['metadata']))
            self.weights = {name: data[name].copy() for name in data.files if name != 'metadata'}
        expected = {k: v for k, v in config.items() if k not in ('model', 'training')}
        if (self.metadata['schema'] != 'atom-sac-actor-v1'
                or self.metadata['model_sha256'] != model_hash
                or self.metadata['config'] != expected):
            raise ValueError('Policy/model/configuration mismatch')

    def predict(self, observation, deterministic=True):
        value = np.asarray(observation, dtype=np.float32)
        if not np.isfinite(value).all():
            raise ValueError('Invalid policy observation')
        for index, kind in enumerate(self.metadata['layers']):
            if kind == 'linear':
                value = value @ self.weights[f'w{index}'].T + self.weights[f'b{index}']
            elif kind == 'relu':
                value = np.maximum(value, 0)
            else:
                raise ValueError('Unsupported policy layer')
        return np.tanh(value), None


def config_signature(config, model_hash):
    payload = dict(config)
    payload.pop('model')
    payload['model_sha256'] = model_hash
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
