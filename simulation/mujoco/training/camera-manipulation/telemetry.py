"""CSV exports for the PPO training run."""
import csv
from contextlib import ExitStack
import json

from torch import nn


REWARD_FIELDS = ('time', 'action', 'approach', 'grasp', 'lift', 'transport',
                 'placement', 'success', 'visual_success', 'neighbor_disturbance',
                 'non_target_contact', 'neighbor_displacement', 'topple', 'failure')
UPDATE_FIELDS = ('learning_rate', 'loss', 'policy_gradient_loss', 'value_loss',
                 'entropy_loss', 'approx_kl', 'clip_fraction', 'clip_range',
                 'clip_range_vf', 'explained_variance', 'std')


class TrainingCsv:
    def __init__(self, output, policy):
        self.last_update = None
        self.episode = 1
        self.episode_return = 0.
        self.streams = ExitStack()
        try:
            self.steps = self.writer(output/'steps.csv', (
                'training_step', 'episode', 'episode_step', 'phase', 'target',
                'reward', 'episode_return', 'done', 'success', 'failure',
                'contact_steps', 'toppled', 'appearance_iou', 'wrist_command_rad',
                'action_values', *(f'reward_{key}' for key in REWARD_FIELDS),
                'reward_components'))
            self.updates = self.writer(output/'ppo_updates.csv', (
                'training_step', 'n_updates', *UPDATE_FIELDS))
            with (output/'network.csv').open('x', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(('module', 'type', 'input_units_or_channels',
                                 'output_units_or_channels', 'parameters', 'trainable_parameters'))
                for name, module in policy.named_modules():
                    parameters = tuple(module.parameters(recurse=False))
                    if not name or (not parameters and any(module.children())):
                        continue
                    dimensions = ((module.in_features, module.out_features) if isinstance(module, nn.Linear)
                                  else (getattr(module, 'in_channels', None),
                                        getattr(module, 'out_channels', None)))
                    writer.writerow((name, type(module).__name__, *dimensions,
                                     sum(p.numel() for p in parameters),
                                     sum(p.numel() for p in parameters if p.requires_grad)))
        except Exception:
            self.close()
            raise

    def writer(self, path, fields):
        stream = self.streams.enter_context(path.open('x', newline='', encoding='utf-8', buffering=1))
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        return writer

    def record_step(self, step, reward, done, action, info):
        self.episode_return += reward
        components = info.get('reward_components') or {}
        row = {key: info.get(key) for key in ('phase', 'target', 'success', 'failure',
               'contact_steps', 'appearance_iou', 'wrist_command_rad')}
        row.update(training_step=step, episode=self.episode,
                   episode_step=info.get('episode_steps'), reward=reward,
                   episode_return=self.episode_return, done=bool(done),
                   toppled=bool(info.get('topple_event')), action_values=json.dumps(action.tolist()),
                   reward_components=json.dumps(components, sort_keys=True))
        row.update({f'reward_{key}': components.get(key, 0.) for key in REWARD_FIELDS})
        self.steps.writerow(row)
        if done:
            self.episode += 1
            self.episode_return = 0.

    def record_update(self, step, metrics):
        count = metrics.get('train/n_updates')
        if count is None or count == self.last_update:
            return
        self.last_update = count
        self.updates.writerow(dict(training_step=step, n_updates=count, **{
            key: metrics.get('train/'+key) for key in UPDATE_FIELDS}))

    def close(self):
        self.streams.close()
