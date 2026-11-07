"""Publish rollout data to a standalone dashboard process."""
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import torch


class DashboardPublisher:
    def __init__(self, output):
        path = output/'dashboard.jsonl'
        self.stream = path.open('x', encoding='utf-8', buffering=1)
        self.activation = {}
        self.hooks = []
        self.last_publish = 0.
        try:
            self.process = subprocess.Popen(
                [sys.executable, '-B', str(Path(__file__).with_name('dashboard.py')), str(path)],
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.write(status='Baseline evaluation — PPO starts after validation')
        except Exception:
            self.stream.close()
            raise

    def attach(self, policy):
        layers = {
            'Features': policy.pi_features_extractor,
            'Actor': policy.mlp_extractor.policy_net,
            'Critic': policy.mlp_extractor.value_net,
            'Action': policy.action_net,
            'Value': policy.value_net,
        }
        for name, layer in layers.items():
            self.hooks.append(layer.register_forward_hook(self.record_activation(name)))
        self.write(status='Collecting PPO experience')

    def record_activation(self, name):
        def capture(module, inputs, output):
            if not torch.is_grad_enabled():
                self.activation[name] = output.detach()
        return capture

    def write(self, **data):
        self.stream.write(json.dumps(data, allow_nan=False)+'\n')

    def update(self, step, reward, info, metrics):
        now = time.monotonic()
        if self.process.poll() is not None or now-self.last_publish < .10:
            return
        self.last_publish = now
        values = {name: tensor.float().square().mean().sqrt().item()
                  for name, tensor in self.activation.items()}
        self.write(step=step, reward=reward if math.isfinite(reward) else None,
                   info={key: info.get(key) for key in (
                       'phase', 'target', 'reward_components', 'failure', 'contact_steps')},
                   activation={name: value for name, value in values.items() if math.isfinite(value)},
                   metrics={key: float(value) for key, value in metrics.items()
                            if key.startswith('train/') and isinstance(value, (int, float))
                            and math.isfinite(value)})

    def close(self, completed=False):
        for hook in self.hooks:
            hook.remove()
        self.write(status='Run complete' if completed else 'Run stopped')
        self.stream.close()
