"""Numerically scaled visual/task fusion for autonomous SB3 policies."""
from torch import nn
from stable_baselines3.common.torch_layers import CombinedExtractor, NatureCNN


POLICY_VERSION = 2


class AutonomousFeatures(CombinedExtractor):
    def __init__(self, observation_space, **kwargs):
        super().__init__(observation_space, **kwargs)
        for encoder in self.extractors.values():
            if isinstance(encoder, NatureCNN):
                encoder.linear.append(nn.LayerNorm(encoder.features_dim))
