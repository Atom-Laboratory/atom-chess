"""Camera/issued-command contextual PPO helpers, with no physics observation API."""
import numpy as np
import torch
from torch import nn
from torch.distributions import Normal

from cem_core import LOWER, UPPER


CONTEXT_KEYS = frozenset(('source_xy_m', 'issued_command', 'squares'))


def context(fields, lower, upper):
    if set(fields) != CONTEXT_KEYS:
        raise ValueError('Context allowlist rejects measured state or unknown features')
    xy, command, squares = (np.asarray(fields[key], dtype=float) for key in ('source_xy_m', 'issued_command', 'squares'))
    lower, upper = np.asarray(lower), np.asarray(upper)
    if xy.shape != (2,) or command.shape != (6,) or squares.shape != (4,) or not all(np.isfinite(a).all() for a in (xy, command, squares)):
        raise ValueError('Finite camera/command/task context required')
    if (lower.shape != (6,) or upper.shape != (6,) or not np.isfinite(lower).all()
            or not np.isfinite(upper).all() or np.any(upper <= lower)):
        raise ValueError('Static compiled normalization limits required')
    if np.any(command < lower) or np.any(command > upper) or np.any(squares < 0) or np.any(squares > 1):
        raise ValueError('Issued command/task context exceeds static bounds')
    return np.concatenate((xy / .5, 2 * (command - lower) / (upper - lower) - 1, 2 * squares - 1)).astype(np.float32)


def physical_reward(record):
    outcome = record.get('outcome', {})
    if not record.get('geometry_valid') or not outcome.get('success') or outcome.get('forbidden_contact', True):
        return -100.
    return 10. - min(float(record['duration_s']) / 40., 1.) - min(float(outcome['maximum_hold_slip_m']) / .003, 1.)


def to_parameters(latent):
    lower = torch.as_tensor(LOWER, dtype=latent.dtype, device=latent.device)
    upper = torch.as_tensor(UPPER, dtype=latent.dtype, device=latent.device)
    return lower + (latent.tanh() + 1) * (upper - lower) / 2


def expert_latent(parameters, *, device):
    value = torch.as_tensor(parameters, dtype=torch.float32, device=device)
    lower = torch.as_tensor(LOWER, dtype=value.dtype, device=device)
    upper = torch.as_tensor(UPPER, dtype=value.dtype, device=device)
    return torch.atanh(torch.clamp(2 * (value - lower) / (upper - lower) - 1, -.999999, .999999))


class ParameterPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        def network(output):
            return nn.Sequential(nn.Linear(12, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, output))
        self.actor, self.critic = network(3), network(1)
        self.log_std = nn.Parameter(torch.full((3,), -2.))

    def distribution(self, observations):
        return Normal(self.actor(observations), self.log_std.clamp(-5., 0.).exp())

    def log_prob(self, observations, latent):
        distribution = self.distribution(observations)
        # Stable log(1-tanh(z)^2), including the affine parameter-map Jacobian.
        correction = 2 * (np.log(2.) - latent - torch.nn.functional.softplus(-2 * latent))
        scale = torch.as_tensor((UPPER - LOWER) / 2, device=latent.device, dtype=latent.dtype)
        return (distribution.log_prob(latent) - correction - scale.log()).sum(-1)

    def value(self, observations):
        return self.critic(observations).squeeze(-1)


def ppo_update(policy, optimizer, observations, latent, old_log_prob, returns, *, epochs=4):
    with torch.no_grad():
        advantage = returns - policy.value(observations)
        advantage = (advantage - advantage.mean()) / advantage.std(unbiased=False).clamp_min(1e-8)
    metrics = {}
    for epoch in range(epochs):
        log_prob = policy.log_prob(observations, latent)
        log_ratio = log_prob - old_log_prob
        ratio = log_ratio.exp()
        approximate_kl = ((ratio - 1) - log_ratio).mean()
        if epoch and float(approximate_kl.detach()) > .03:
            break
        policy_loss = -torch.minimum(ratio * advantage, ratio.clamp(.8, 1.2) * advantage).mean()
        value_loss = torch.nn.functional.mse_loss(policy.value(observations), returns)
        # This is base-Gaussian entropy, explicitly not exact transformed entropy.
        base_entropy = policy.distribution(observations).entropy().sum(-1).mean()
        loss = policy_loss + .5 * value_loss - .001 * base_entropy
        optimizer.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(policy.parameters(), .5)
        optimizer.step()
        metrics = dict(loss=float(loss.detach()), policy_loss=float(policy_loss.detach()), value_loss=float(value_loss.detach()),
            base_gaussian_entropy=float(base_entropy.detach()), approximate_kl=float(approximate_kl.detach()),
            clip_fraction=float(((ratio - 1).abs() > .2).float().mean().detach()), optimizer_epochs=epoch + 1)
    return metrics
