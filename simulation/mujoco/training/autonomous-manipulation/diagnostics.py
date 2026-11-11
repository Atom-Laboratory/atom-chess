"""Bounded forward/backward/device and checkpoint checks on the actual actor."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import time

import numpy as np
import torch
from stable_baselines3 import PPO

from atom_mujoco.autonomous_env import AutonomousManipulationEnv
from atom_mujoco.autonomous_policy import AutonomousFeatures, POLICY_VERSION
from atom_mujoco.paths import new_run
from run import save_checkpoint, weights_sha


def gpu_sample():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,utilization.gpu,memory.used,temperature.gpu',
            '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True, timeout=5)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError) as error:
        return dict(unavailable=repr(error))


def benchmark(env, observation, device, batch_size, output):
    policy = PPO('MultiInputPolicy', env, n_steps=32, batch_size=32, n_epochs=2,
                 device=device, seed=7, policy_kwargs={'features_extractor_class': AutonomousFeatures}).policy
    optimizer = policy.optimizer
    batch = {key: np.repeat(value[None], batch_size, axis=0) for key, value in observation.items()}
    inputs = policy.obs_to_tensor(batch)[0]
    assert all(value.device.type == device for value in inputs.values())
    assert all(value.device.type == device for value in policy.parameters())
    before = {name: value.detach().cpu().clone() for name, value in policy.named_parameters()}
    times, gradients = [], []
    for index in range(8):
        if device == 'cuda':
            torch.cuda.synchronize()
        started = time.perf_counter()
        actions, values, log_prob = policy(inputs)
        loss = values.square().mean()-.01*log_prob.mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grads = [param.grad for param in policy.parameters() if param.grad is not None]
        assert grads and all(grad.device.type == device and torch.isfinite(grad).all() for grad in grads)
        gradients.append(float(torch.linalg.vector_norm(torch.stack([grad.norm() for grad in grads])).item()))
        optimizer.step()
        if device == 'cuda':
            torch.cuda.synchronize()
        elapsed = time.perf_counter()-started
        if index >= 2:
            times.append(elapsed)
    assert all(np.isfinite(gradients)) and any(value > 0 for value in gradients)
    assert any(not torch.equal(before[name], value.detach().cpu()) for name, value in policy.named_parameters())
    states = [value for state in optimizer.state.values() for key, value in state.items()
              if isinstance(value, torch.Tensor) and key != 'step']
    assert states and all(value.device.type == device for value in states)
    # Use the actual SB3 container and archive format for reload verification.
    model = PPO('MultiInputPolicy', env, n_steps=32, batch_size=32, device=device, seed=7,
                policy_kwargs={'features_extractor_class': AutonomousFeatures})
    model.policy = policy
    digest = save_checkpoint(model, output/f'{device}-policy.zip')
    restored = PPO.load(output/f'{device}-policy.zip', device=device)
    assert weights_sha(model) == weights_sha(restored)
    original_states = model.policy.optimizer.state_dict()['state']
    loaded_states = restored.policy.optimizer.state_dict()['state']
    assert original_states.keys() == loaded_states.keys()
    for parameter, state in original_states.items():
        for key, value in state.items():
            torch.testing.assert_close(value.cpu(), loaded_states[parameter][key].cpu(), rtol=0, atol=0)
    return dict(device=device, batch_size=batch_size, updates=8, timed_updates=len(times),
                gradient_norms=gradients,
                median_update_s=float(np.median(times)), samples_per_s=batch_size/float(np.median(times)),
                finite_nonzero_gradients=True, parameters_changed=True, inputs_on_device=True,
                parameters_on_device=True, gradients_on_device=True, adam_state_on_device=True,
                checkpoint_reload_verified=True, optimizer_reload_verified=True, checkpoint_sha256=digest,
                allocated_bytes=torch.cuda.memory_allocated() if device == 'cuda' else None,
                reserved_bytes=torch.cuda.memory_reserved() if device == 'cuda' else None,
                hardware=gpu_sample() if device == 'cuda' else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--batch-size', type=int, default=64)
    args = parser.parse_args()
    if args.batch_size < 2:
        parser.error('Batch size must be at least two')
    if not torch.cuda.is_available():
        parser.error('CUDA is required for the matched diagnostic')
    output = args.output or new_run('training/autonomous-manipulation/runs')
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    env = AutonomousManipulationEnv(args.config, objective='reach')
    try:
        observation, _ = env.reset(seed=7)
        results = [benchmark(env, observation, device, args.batch_size, output) for device in ('cpu', 'cuda')]
        report = dict(schema=1, environment_version=env.VERSION, policy_version=POLICY_VERSION, torch=torch.__version__,
                      cuda=torch.version.cuda, gpu=torch.cuda.get_device_name(),
                      cpu_threads=torch.get_num_threads(), config=str(args.config.resolve()),
                      scope='actual policy forward/backward/Adam updates, excluding physics and rollout',
                      observation_snapshot={key: dict(shape=list(value.shape), min=float(value.min()),
                          max=float(value.max()), mean=float(value.mean()), std=float(value.std()))
                          for key, value in observation.items()},
                      results=results, cuda_speedup=results[0]['median_update_s']/results[1]['median_update_s'])
        (output/'diagnostic.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        with (output/'benchmark.csv').open('x', newline='', encoding='utf-8') as stream:
            fields = ('device', 'batch_size', 'median_update_s', 'samples_per_s', 'allocated_bytes', 'reserved_bytes')
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
        print(json.dumps(report, indent=2), flush=True)
    except BaseException as error:
        (output/'failure.json').write_text(json.dumps(dict(error=repr(error))), encoding='utf-8')
        raise
    finally:
        env.close()


if __name__ == '__main__':
    main()
