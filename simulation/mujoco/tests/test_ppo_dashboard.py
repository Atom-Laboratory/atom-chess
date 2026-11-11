from collections import deque
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


LAUNCHER = Path(__file__).resolve().parents[1]/'training/camera-manipulation'


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, LAUNCHER/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_update_ingest_uses_optimizer_step_and_keeps_final_packet(monkeypatch):
    monkeypatch.syspath_prepend(str(LAUNCHER))
    dashboard = load_module('dashboard')
    view = dashboard.TrainingDashboard.__new__(dashboard.TrainingDashboard)
    view.last_update = None
    view.loss_history = {'loss': deque()}
    for step, count, loss in [(32, 2, 10.), (32, 2, 30.), (64, 4, -5.)]:
        view.ingest({'update': {'step': step, 'metrics': {'train/n_updates': count, 'train/loss': loss}}})
    assert view.update_step == 64
    assert list(view.loss_history['loss']) == [(32, 10., 10.), (64, -5., 7.)]


def test_dashboard_graph_tracks_actual_feature_and_head_modules():
    torch = pytest.importorskip('torch')
    pytest.importorskip('stable_baselines3')
    from gymnasium import spaces
    from stable_baselines3.common.policies import MultiInputActorCriticPolicy

    policy = MultiInputActorCriticPolicy(
        spaces.Dict(image=spaces.Box(0, 255, (3, 96, 96), dtype='uint8'),
                    task=spaces.Box(0., 1., (4,))),
        spaces.Box(-1., 1., (5,)), lambda _: .001,
        net_arch={'pi': [12, 8], 'vf': [7]})
    graph, hooks = load_module('dashboard_publisher').policy_graph(policy)
    by_id = {node['id']: node for node in graph}
    assert [node['label'] for node in graph if node['column'] == 3] == ['Actor 12', 'Actor 8', 'Critic 7']
    assert by_id['features']['parents'] == ['Projection-0', 'task']
    assert by_id['action']['parents'] == ['Actor-2']
    assert hooks['action'] is policy.action_net
    assert isinstance(hooks['Actor-2'], torch.nn.Tanh)


def test_progress_shares_stage_and_count_with_terminal_and_dashboard(capsys):
    progress = load_module('run_progress').RunProgress()
    events = []
    progress.dashboard = SimpleNamespace(write=lambda **event: events.append(event['progress']))
    progress.stage('Training PPO', total=2048, unit='steps')
    progress.advance(200, 'APPROACH', force=True)
    progress.stage('Evaluating saved policy', total=1, unit='episodes')

    lines = capsys.readouterr().out.splitlines()
    assert lines[1] == '[ATOM] Training PPO | 200/2048 steps (9.8%) | APPROACH'
    assert events[1] == dict(stage='Training PPO', completed=200, total=2048,
                             unit='steps', detail='APPROACH')
    assert events[2]['completed'] == 0 and events[2]['unit'] == 'episodes'


def test_autonomous_visual_fusion_is_normalized_and_has_finite_gradients():
    import numpy as np
    import torch
    from gymnasium import spaces
    from stable_baselines3.common.policies import MultiInputActorCriticPolicy
    from atom_mujoco.autonomous_policy import AutonomousFeatures
    observation_space = spaces.Dict(image=spaces.Box(0, 255, (6, 96, 96), dtype=np.uint8),
                                    visual_target=spaces.Box(-1., 1., (5,), dtype=np.float32))
    policy = MultiInputActorCriticPolicy(observation_space, spaces.Box(-1., 1., (7,)),
        lambda _: .0003, features_extractor_class=AutonomousFeatures)
    batch = {'image': torch.randint(0, 256, (4, 6, 96, 96)),
             'visual_target': torch.tensor([[.2, .1, .3, 1, 0], [-.2, -.1, .4, 1, 0],
                                            [.1, -.3, .2, 1, 0], [-.1, .3, .5, 1, 0]])}
    encoder = policy.features_extractor.extractors['image']
    features = encoder(batch['image'].float()/255)
    torch.testing.assert_close(features.mean(dim=1), torch.zeros(4), atol=1e-5, rtol=0)
    assert torch.all((features.square().mean(dim=1) > .99) & (features.square().mean(dim=1) < 1.01))
    _, values, probabilities = policy(batch)
    (values.square().mean()-.01*probabilities.mean()).backward()
    gradients = [p.grad for p in policy.parameters() if p.grad is not None]
    assert all(torch.isfinite(gradient).all() for gradient in gradients)
    assert values.std() > 1e-6
    graph, _ = load_module('dashboard_publisher').policy_graph(policy, action_description='continuous temporal controls')
    assert any(node['label'] == 'Visual LayerNorm' for node in graph)
