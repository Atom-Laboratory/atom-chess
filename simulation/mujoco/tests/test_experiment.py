"""Infrastructure tests with toy tasks, not a reaching formulation or agent."""
from pathlib import Path
import json
import subprocess

import mujoco
import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.experiment import Episode
from atom_mujoco.model import build_bundle
from atom_mujoco.recording import provenance, save_record


class DiagnosticTask:
    def reset(self, state, rng):
        self.marker = rng.random()

    def observation(self, state):
        return state['position']

    def target(self, action, state):
        return action

    def evaluate(self, before, after):
        return 0., False, {'marker': self.marker}  # Test double only.


def test_episode_reset_replay_truncation_and_rejected_action(sim):
    episode = Episode(sim, DiagnosticTask(), max_steps=2)
    with pytest.raises(RuntimeError):
        episode.step([0, 0, 0])
    first, _ = episode.reset(seed=31, randomize=True)
    with pytest.raises(ValueError):
        episode.step([99, 0, 0])
    assert sim.data.time == 0 and episode.steps == 0
    transition = episode.step([.2, .04, -.2])
    assert transition[1:4] == (0., False, False)
    assert episode.step([.2, .04, -.2])[3]
    with pytest.raises(RuntimeError):
        episode.step([0, 0, 0])
    repeated, _ = episode.reset(seed=31, randomize=True)
    np.testing.assert_array_equal(first, repeated)
    replay = episode.step([.2, .04, -.2])
    np.testing.assert_array_equal(transition[0], replay[0])
    assert transition[4]['task'] == replay[4]['task']


def test_task_termination_and_failed_reward_require_reset(sim):
    task = DiagnosticTask()
    episode = Episode(sim, task, max_steps=10)
    episode.reset(seed=0)
    task.evaluate = lambda before, after: (1., True, {})
    assert episode.step([0, 0, 0])[2:4] == (True, False)
    episode.reset(seed=0)
    task.evaluate = lambda before, after: (float('nan'), False, {})
    with pytest.raises(ValueError):
        episode.step([0, 0, 0])
    with pytest.raises(RuntimeError):
        episode.step([0, 0, 0])


def test_configured_tool_pose_matches_rigid_transform(tmp_path):
    source = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    output = tmp_path/'tool'
    offset = [.12, .01, -.02]  # Arbitrary fixture, not a CAD measurement.
    build_bundle(source, output, parameters={'tool_offset_in_arm2_m': offset, 'actuator_kp': 40.})
    sim = Simulation(output)
    for position in ([0, 0, 0], [.3, .05, .8]):
        state = sim.reset(position)
        expected = state['arm2_position'] + state['arm2_rotation'] @ offset
        np.testing.assert_allclose(state['tool_pose']['position_m'], expected, atol=1e-12)
        assert not state['tool_pose']['tcp_calibrated']
    assert sim.manifest['profile']['actuator_kp'] == 40.


@pytest.mark.parametrize('parameters', [{'gravity': [0,0,-9.81]}, {'actuator_kp': -1},
                         {'control_substeps': 1.5}, {'diagonal_inertia_kg_m2': [1,1,4]},
                         {'tool_offset_in_arm2_m': [0,0,float('nan')]}])
def test_invalid_parameters_write_nothing(tmp_path, parameters):
    source = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    with pytest.raises(ValueError):
        build_bundle(source, tmp_path/'invalid', parameters=parameters)
    assert not (tmp_path/'invalid').exists()


def test_engine_contact_fixture_is_distinct_from_robot(sim):
    # Validates the installed engine, NOT robot collisions. All fixture values
    # are synthetic SI values; the robot still declares contacts unavailable.
    model = mujoco.MjModel.from_xml_string('''<mujoco>
      <option timestep="0.002" gravity="0 0 -9.81"/>
      <worldbody><geom name="floor" type="plane" size="1 1 .1"/>
      <body pos="0 0 .2"><freejoint/><geom name="ball" type="sphere"
        size=".05" mass=".1"/></body></worldbody></mujoco>''')
    data = mujoco.MjData(model)
    for _ in range(500):
        mujoco.mj_step(model, data)
    assert data.ncon > 0 and .045 < data.qpos[2] < .055
    force = np.zeros(6)
    mujoco.mj_contactForce(model, data, 0, force)
    assert force[0] > 0
    assert np.isfinite(data.qpos).all()
    assert sim.observe()['contacts'] is None
    assert sim.model.opt.disableflags & mujoco.mjtDisableBit.mjDSBL_CONTACT


def test_record_roundtrip_no_overwrite_and_nonfinite_rejected(tmp_path):
    output = tmp_path/'record.json'
    save_record(output, {'provenance': provenance(), 'values': np.array([1.,2.])})
    before = output.read_bytes()
    assert json.loads(before)['values'] == [1.,2.]
    with pytest.raises(FileExistsError):
        save_record(output, {})
    assert output.read_bytes() == before
    with pytest.raises(ValueError):
        save_record(tmp_path/'bad.json', {'value': float('nan')})
    assert not (tmp_path/'bad.json').exists()


def test_provenance_sees_untracked_files_outside_package(tmp_path, monkeypatch):
    from atom_mujoco import recording
    def git(*args):
        subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True)
    git('init')
    (tmp_path/'tracked.txt').write_text('fixture')
    git('add', 'tracked.txt')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'fixture')
    package = tmp_path/'package'
    package.mkdir()
    monkeypatch.setattr(recording, '__file__', str(package/'recording.py'))
    assert recording.provenance()['untracked_present'] is False
    (tmp_path/'task.py').write_text('# researcher task outside package')
    metadata = recording.provenance()
    assert metadata['untracked_present'] is True
    assert metadata['tracked_dirty'] is False


def test_cli_parameters_accept_windows_utf8_bom(tmp_path, monkeypatch, capsys):
    from atom_mujoco.cli import main
    source = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    config = tmp_path/'config.json'
    config.write_text('{"actuator_kp": 40}', encoding='utf-8-sig')
    monkeypatch.setattr('sys.argv', ['atom-mujoco', 'build', '--urdf', str(source),
                                   '--output', str(tmp_path/'bundle'), '--parameters', str(config)])
    main()
    assert json.loads(capsys.readouterr().out)['profile']['actuator_kp'] == 40
