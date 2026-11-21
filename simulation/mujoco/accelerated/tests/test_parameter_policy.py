import sys
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip('torch')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parameter_policy import ParameterPolicy, context, physical_reward, ppo_update, to_parameters
from train_parameters import checkpoint, restore


def test_actor_context_rejects_physics_truth_and_preserves_command_semantics():
    fields = dict(source_xy_m=[.25, -.08], issued_command=np.zeros(6), squares=[.5, .2, .5, .4])
    assert context(fields, -np.ones(6), np.ones(6)).shape == (12,)
    for name in ('qpos', 'object_position', 'contacts', 'success'):
        with pytest.raises(ValueError, match='allowlist'):
            context(dict(fields, **{name: [0.]}), -np.ones(6), np.ones(6))


def test_recorded_inference_adapter_ignores_actual_qpos_and_qvel(tmp_path, monkeypatch):
    import mujoco
    from types import SimpleNamespace
    import evaluate_policy as inference
    model = mujoco.MjModel.from_xml_string('<mujoco><worldbody>' + ''.join(
        f'<body><joint name="j{i}" type="slide"/><geom size=".01"/></body>' for i in range(6))
        + '</worldbody><actuator>' + ''.join(f'<motor joint="j{i}"/>' for i in range(6)) + '</actuator></mujoco>')
    sim = SimpleNamespace(model=model, lower=-np.ones(6), upper=np.ones(6), manifest=dict(model_sha256='test'))
    reference = dict(stages=[dict(name='DESCEND', target=[.25, -.08, .04])])
    monkeypatch.setattr(inference, 'validated_reference', lambda *a: reference)
    saved = []
    monkeypatch.setattr(inference, 'load_recording', lambda *a: (np.array(saved), None, np.array(['CLOSE']), {}))
    data = mujoco.MjData(model); data.ctrl[:] = .1
    state = np.empty(mujoco.mj_stateSize(model, inference.SIGNATURE))
    mujoco.mj_getState(model, data, state, inference.SIGNATURE); saved[:] = [state.copy()]
    first, fields = inference.reference_context(dict(source='e2', target='e4'), sim, tmp_path)
    data.qpos[:] = 100.; data.qvel[:] = -10.
    mujoco.mj_getState(model, data, state, inference.SIGNATURE); saved[:] = [state.copy()]
    second, _ = inference.reference_context(dict(source='e2', target='e4'), sim, tmp_path)
    np.testing.assert_array_equal(first, second)
    assert fields['issued_command'] == [.1] * 6


def test_action_transform_and_log_density_match_pytorch_transformed_distribution():
    policy = ParameterPolicy()
    observations = torch.zeros((4, 12))
    latent = torch.tensor([[-3., -.2, 2.], [1., .5, -.1], [.1, 0., -.9], [.4, .2, -.3]])
    from cem_core import LOWER, UPPER
    scale = torch.tensor((UPPER - LOWER) / 2, dtype=torch.float32)
    location = torch.tensor((UPPER + LOWER) / 2, dtype=torch.float32)
    transformed = torch.distributions.TransformedDistribution(policy.distribution(observations),
        [torch.distributions.transforms.TanhTransform(), torch.distributions.transforms.AffineTransform(location, scale)])
    action = to_parameters(latent)
    torch.testing.assert_close(policy.log_prob(observations, latent), transformed.log_prob(action).sum(-1), atol=3e-5, rtol=3e-5)
    assert bool(torch.all(action >= torch.tensor(LOWER)) and torch.all(action <= torch.tensor(UPPER)))


def test_failed_grasp_or_forbidden_contact_never_receives_positive_reward():
    successful = dict(geometry_valid=True, duration_s=10., outcome=dict(success=True, forbidden_contact=False, maximum_hold_slip_m=.001))
    assert 8. <= physical_reward(successful) <= 10.
    for mutation in (dict(geometry_valid=False), dict(outcome=dict(success=False, forbidden_contact=False)),
                     dict(outcome=dict(success=True, forbidden_contact=True))):
        assert physical_reward(dict(successful, **mutation)) == -100.


def test_ppo_updates_weights_and_checkpoint_restores_rng_optimizer_and_predictions(tmp_path):
    torch.manual_seed(15)
    policy = ParameterPolicy(); optimizer = torch.optim.Adam(policy.parameters(), lr=.0003)
    observations = torch.randn((8, 12))
    with torch.no_grad():
        latent = policy.distribution(observations).sample()
        log_prob = policy.log_prob(observations, latent)
    before = policy.actor(observations).detach().clone()
    metrics = ppo_update(policy, optimizer, observations, latent, log_prob, torch.arange(8.), epochs=2)
    assert np.isfinite(metrics['loss'])
    assert not torch.equal(before, policy.actor(observations))
    path = tmp_path / 'policy.pt'
    identity = dict(schema='test', input_sha256='bound')
    checkpoint(path, policy, optimizer, identity, 2, 9., 0)
    expected_sample = policy.distribution(observations).sample()
    resumed = ParameterPolicy(); resumed_optimizer = torch.optim.Adam(resumed.parameters())
    assert restore(path, resumed, resumed_optimizer, identity, 'cpu') == (2, 9., 0)
    torch.testing.assert_close(expected_sample, resumed.distribution(observations).sample(), rtol=0, atol=0)
    torch.testing.assert_close(policy.actor(observations), resumed.actor(observations), rtol=0, atol=0)
    assert resumed_optimizer.state_dict()['state']
    with pytest.raises(ValueError, match='identity'):
        restore(path, resumed, resumed_optimizer, dict(schema='other'), 'cpu')
