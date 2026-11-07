"""Publish rollout data to a standalone dashboard process."""
import json
import math
from numbers import Real
from pathlib import Path
import subprocess
import sys
import time

import torch
from torch import nn


def policy_graph(policy):
    """Describe the actual P038 MultiInputPolicy, with activations grouped by layer."""
    graph, hooks = [], {}

    def node(key, label, column, parents=(), detail='', layer=None, hook=None):
        parameters = sum(p.numel() for p in layer.parameters()) if layer is not None else 0
        graph.append(dict(id=key, label=label, column=column, parents=list(parents),
                          detail=detail, parameters=parameters))
        if hook is not None:
            hooks[key] = hook
        return key

    def sequence(prefix, layers, column, parent):
        layers = list(layers)
        for index, layer in enumerate(layers):
            if not isinstance(layer, (nn.Conv2d, nn.Linear)):
                continue
            following = layers[index+1] if index+1 < len(layers) else None
            activation = following if isinstance(following, (nn.ReLU, nn.Tanh)) else None
            if isinstance(layer, nn.Conv2d):
                detail = f'{layer.in_channels} → {layer.out_channels} channels, {layer.kernel_size[0]}×{layer.kernel_size[1]}'
                label = f'Conv {layer.out_channels}'
            else:
                detail = f'{layer.in_features} → {layer.out_features} units'
                label = f'{prefix} {layer.out_features}'
            if activation is not None:
                detail += f' · {type(activation).__name__}'
            parent = node(f'{prefix}-{index}', label, column, [parent],
                          detail, layer, activation if activation is not None else layer)
        return parent

    extractor = policy.pi_features_extractor
    image_encoder = extractor.extractors['image']
    image = node('image', 'RGB image', 0, detail=' × '.join(map(str, policy.observation_space['image'].shape)))
    encoded = sequence('CNN', image_encoder.cnn, 1, image)
    encoded = sequence('Projection', image_encoder.linear, 1, encoded)
    names = {'task': 'Source / target', 'commanded_joints': 'Commanded joints',
             'previous_action': 'Previous action', 'phase': 'Motion phase',
             'perception_valid': 'Perception valid'}
    inputs = [encoded]
    for name, encoder in extractor.extractors.items():
        if name != 'image':
            inputs.append(node(name, names.get(name, name), 0,
                               detail=f'{encoder.__class__.__name__} input',
                               hook=encoder))
    features = node('features', 'Concatenate', 2, inputs,
                    f'{extractor.features_dim} features', hook=extractor)
    actor = sequence('Actor', policy.mlp_extractor.policy_net, 3, features)
    critic = sequence('Critic', policy.mlp_extractor.value_net, 3, features)
    node('action', 'Action mean μ', 4, [actor], f'{policy.action_net.out_features} residual controls',
         policy.action_net, policy.action_net)
    node('value', 'State value V', 4, [critic], 'Predicted discounted return',
         policy.value_net, policy.value_net)
    return graph, hooks


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
        except Exception:
            self.stream.close()
            raise

    def attach(self, policy):
        graph, layers = policy_graph(policy)
        for name, layer in layers.items():
            self.hooks.append(layer.register_forward_hook(self.record_activation(name)))
        self.write(graph=graph,
                   trainable_parameters=sum(p.numel() for p in policy.parameters() if p.requires_grad))

    def record_activation(self, name):
        def capture(module, inputs, output):
            if not torch.is_grad_enabled():
                self.activation[name] = output.detach()
        return capture

    def write(self, **data):
        self.stream.write(json.dumps(data, allow_nan=False)+'\n')

    def optimization(self, step, metrics):
        self.write(update=dict(step=step, metrics={
            key: float(value) for key, value in metrics.items()
            if key.startswith(('train/', 'rollout/', 'time/')) and isinstance(value, Real)
            and math.isfinite(value)}))

    def update(self, step, reward, info):
        now = time.monotonic()
        if self.process.poll() is not None or now-self.last_publish < .10:
            return
        self.last_publish = now
        values = []
        for tensor in self.activation.values():
            tensor = tensor.float()
            values.append(torch.stack((tensor.square().mean().sqrt(), tensor.abs().max(),
                                       (tensor != 0).float().mean())))
        values = torch.stack(values).cpu().tolist() if values else []
        activation = {
            name: dict(rms=value[0], peak=value[1], active=value[2],
                       shape=list(self.activation[name].shape[1:]))
            for name, value in zip(self.activation, values) if all(map(math.isfinite, value))}
        self.write(step=step, reward=reward if math.isfinite(reward) else None,
                   info={key: info.get(key) for key in (
                       'phase', 'target', 'reward_components', 'episode_reward_components',
                       'failure', 'contact_steps', 'topple_event', 'episode_steps')},
                   activation=activation)

    def close(self):
        for hook in self.hooks:
            hook.remove()
        self.stream.close()
