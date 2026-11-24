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
