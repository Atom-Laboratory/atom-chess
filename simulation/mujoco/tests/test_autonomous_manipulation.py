import os
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from atom_mujoco.autonomous_control import AutonomousControl, MotionChoice
from atom_mujoco.autonomous_observation import VisualHistory


def test_interpolation_respects_exact_validated_bounds():
    from atom_mujoco.autonomous_control import interpolate_command
    lower = np.array([-2., -.1, -2., -.021, -.021, 0.])
    upper = np.array([2., .2, 4., 0., 0., 2*np.pi])
    rng = np.random.default_rng(7)
    for count in range(1, 11):
        for end in (lower, upper):
            start = rng.uniform(lower, upper)
            start[4] = start[3]
            for index in range(1, count+1):
                goal = interpolate_command(start, end, index, count)
                assert np.all(lower <= goal) and np.all(goal <= upper)
                assert goal[3] == goal[4]
            np.testing.assert_array_equal(goal, end)


def test_piece_height_uses_collision_geometry_and_correct_box_axis():
    import mujoco
    from atom_mujoco.autonomous_scene import collision_height
    model = mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
      <body name="king"><geom type="box" size=".02 .01 .04" pos="0 0 .04"/>
        <geom type="sphere" size="1" pos="0 0 2" contype="0" conaffinity="0"/>
      </body></worldbody></mujoco>''')
    assert collision_height(model, 'king') == pytest.approx(.08)


def test_reward_has_signed_progress_and_proportional_neighbor_cost():
    from atom_mujoco.autonomous_feedback import ManipulationFeedback
    feedback = ManipulationFeedback.__new__(ManipulationFeedback)
    guard = SimpleNamespace(displacements_mm=lambda: {}, step_events={},
                            displacement_delta_mm=0., topple_event=None)
    feedback.base = SimpleNamespace(piece_height=.05, contact_guard=guard,
        config={'reward_weights': {'grasp': 2., 'lift': 3., 'success': 10.}},
        contact_penalty=20., displacement_penalty_per_mm=1., dwell=10)
    feedback.sim = SimpleNamespace(data=SimpleNamespace(xpos=np.zeros((1, 3))))
    feedback.scene = SimpleNamespace(grip_contacts=lambda _: False, settled=lambda _: True)
    feedback.piece, feedback.body, feedback.origin_z = 'pawn', 0, 0.
    feedback.previous, feedback.initial_distance, feedback.best_distance = -4., .2, .2
    feedback.events, feedback.hold, feedback.reach_threshold = set(), 0, .035
    feedback.proximity = lambda: -2.
    reward, info = feedback.evaluate(np.zeros(7), {'status': 'ACCEPTED'}, 'reach', None)
    assert reward['proximity'] == pytest.approx(2.) and not info['success']
    feedback.proximity = lambda: -3.
    guard.displacement_delta_mm = 2.5
    guard.step_events = {'contact': True}
    reward, info = feedback.evaluate(np.zeros(7), {'status': 'ACCEPTED'}, 'reach', None)
    assert reward['proximity'] == pytest.approx(-1.)
    assert reward['neighbor_displacement'] == -2.5
    assert reward['non_target_contact'] == -20.
    assert info['best_pad_distance_m'] == pytest.approx(.1)


def frame(valid=True):
    return SimpleNamespace(rectified_rgb=np.full((800, 800, 3), 120, dtype=np.uint8),
                           oriented=valid, homography=np.eye(3) if valid else None,
                           reference_sha256='board')


def test_visual_payload_is_detached_and_tracks_history():
    history = VisualHistory()
    rgb = frame()
    first = history.observe(rgb, np.zeros(6), np.zeros(7), 'e2', 'e4')
    rgb.rectified_rgb[:] = 240
    second = history.observe(rgb, np.ones(6), np.ones(7), 'e2', 'e4')
    assert first['image'].shape == (6, 96, 96)
    assert np.all(first['image'] == 120)
    assert np.all(second['image'][:3] == 120) and np.all(second['image'][3:] == 240)
    assert np.all(second['command_history'][:6] == 0)
    invalid = history.observe(frame(False), np.ones(6), np.zeros(7), 'e2', 'e4')
    assert invalid['perception_valid'][0] == 0 and not invalid['image'][3:].any()


def test_actions_accumulate_full_motion_and_remain_fixed_for_duration():
    control = AutonomousControl.__new__(AutonomousControl)
    control.sim = SimpleNamespace(dt=.02, lower=[-1.]*6, upper=[4.]*6)
    control.rates = np.array([1., 1., .5, np.pi, .025])
    control.max_intervals = 10
    control.commanded_tcp = lambda command: np.array([command[0], command[2], command[1]])
    command = np.array([.2, .1, 0., 0., 0., 1.])
    choice = control.decode([.5, 0, -.5, .5, -.5, -1, 1], command)
    assert choice.intervals == 10 and choice.duration_s == pytest.approx(.2)
    assert choice.xyz_m == pytest.approx((.3, 0., .05))
    assert choice.opening_m == pytest.approx(-.0025)
    assert choice.elbow_down is False
    assert choice.wrist_rad == pytest.approx(1.+.1*np.pi)
    with pytest.raises(ValueError):
        control.decode([2., 0, 0, 0, 0, 0, 0], command)


def test_projection_shortens_request_and_still_requires_collision_validation():
    control = AutonomousControl.__new__(AutonomousControl)
    control.model = None
    control.sim = SimpleNamespace(speed=np.ones(6), validate=np.asarray)
    control.commanded_tcp = lambda _: np.zeros(3)
    control.base = SimpleNamespace(motion=SimpleNamespace(
        solve=lambda xyz, opening, wrist, elbow_down: [xyz[0], 0, 0, opening, opening, wrist]))
    calls = []

    def sweep(target, scale):
        calls.append((target, scale))
        return None, {'status': 'SWEEP_REJECTED'}

    control.sweep = sweep
    choice = MotionChoice((.4, 0, 0), .2, -.1, False, 10, .2)
    result, verdict = control.validate(choice, np.zeros(6), project=True)
    assert result is None and verdict['status'] == 'SWEEP_REJECTED'
    assert len(calls) == 1 and calls[0][1] == .5
    np.testing.assert_allclose(calls[0][0], [.2, 0, 0, -.05, -.05, .1])


def test_recorder_accepts_gym_monitor_episode_and_excludes_terminal_images(monkeypatch):
    folder = Path(__file__).resolve().parents[1]/'training'
    monkeypatch.syspath_prepend(str(folder/'camera-manipulation'))
    spec = importlib.util.spec_from_file_location('autonomous_runner', folder/'autonomous-manipulation/run.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    recorder = runner.Recorder.__new__(runner.Recorder)
    recorder.locals = dict(infos=[dict(episode={'r': -1., 'l': 1},
        terminal_observation={'image': np.zeros((6, 96, 96))},
        validation={'status': 'VELOCITY_REJECTED'}, choice={'xyz_m': [0., 0., .1],
        'wrist_rad': 1., 'elbow_down': True})], clipped_actions=[np.zeros(7)],
        rewards=[-1.], dones=[True])
    recorder.scene = SimpleNamespace(base=SimpleNamespace(sim=SimpleNamespace(
        manifest={'scene': {'square_size_m': .035}})))
    from collections import Counter
    recorder.validations, recorder.coverage = Counter(), Counter()
    recorder.stream = io.StringIO()
    recorder.csv = SimpleNamespace(record_step=lambda *args: None)
    recorder.progress = SimpleNamespace(advance=lambda *args: None)
    recorder.num_timesteps, recorder.episode, recorder.next_checkpoint = 1, 1, 512
    recorder.completed, recorder.watch = [], None
    recorder.dashboard = None
    recorder.performance = SimpleNamespace(writerow=lambda row: None)
    assert recorder._on_step()
    event = json.loads(recorder.stream.getvalue())
    assert event['episode_index'] == 1 and event['episode']['l'] == 1
    assert 'terminal_observation' not in event


@pytest.mark.skipif(not os.environ.get('ATOM_AUTONOMOUS_CONFIG'),
                    reason='Requires the native full-board camera fixture')
def test_hidden_physics_isolation_and_rejected_action_never_moves_scene():
    from atom_mujoco.autonomous_env import AutonomousManipulationEnv

    env = AutonomousManipulationEnv(os.environ['ATOM_AUTONOMOUS_CONFIG'], horizon=4)
    try:
        observation, _ = env.reset(seed=100007)
        camera = env.last_frame
        before = env.sim.data.qpos.copy()
        # Identical visual/host histories, different privileged scene states.
        env.history.clear()
        original = env._observation(camera)
        env.sim.data.qpos[:] += .1
        env.history.clear()
        altered = env._observation(camera)
        for key in original:
            np.testing.assert_array_equal(original[key], altered[key])
        env.sim.data.qpos[:] = before
        import mujoco
        mujoco.mj_forward(env.sim.model, env.sim.data)
        assert observation['image'].shape == (6, 96, 96)
        choice = MotionChoice((999., 999., 999.), 1., -.01, True, 10, .2)
        goal, verdict = env.control.validate(choice, env.command)
        assert goal is None and verdict['status'] == 'IK_OR_LIMIT_REJECTED'
        np.testing.assert_array_equal(env.sim.data.qpos, before)

        # A path into the king is rejected even with enough allotted time.
        blocked = MotionChoice(tuple(env.base.source[:2])+(.05,), np.radians(72),
                               0., True, 200, 4.)
        goal, verdict = env.control.validate(blocked, env.command)
        assert goal is None and verdict['status'] == 'SWEEP_REJECTED'
        np.testing.assert_array_equal(env.sim.data.qpos, before)

        # On the same blocked path the optimized and original sweep agree.
        checker = env.control.checker
        end = env.base.motion.solve(blocked.xyz_m, blocked.opening_m, wrist=blocked.wrist_rad)
        checker.samples = 0
        plain = checker.interval(before[env.sim.qadr], end, allowed=env.control.allowed)
        assert plain == verdict['failure']

        # Invalid perception blocks the next command and closes the attempt.
        env.perception_valid = False
        _, _, terminal, _, info = env.step(np.array([0, 0, 0, 0, 0, 1, 0], dtype=np.float32))
        assert terminal and not info['applied'] and info['failure'] == 'PERCEPTION_LOST'
        np.testing.assert_array_equal(env.sim.data.qpos, before)

        env.reset(seed=100007)
        tcp = env.sim.data.site('grasp_center').xpos.copy()
        action = np.array([.2, 0, -.1, .2, 0, 0, -.5], dtype=np.float32)
        _, _, terminal, _, info = env.step(action)
        assert not terminal and info['validation']['status'] == 'ACCEPTED'
        assert info['applied'] and len(info['executed_path']) == info['choice']['intervals']
        displacement = np.asarray(info['executed_path'][-1])-tcp
        assert displacement[0] > 0 and np.linalg.norm(displacement) > .0005
    finally:
        env.close()


@pytest.mark.skipif(not os.environ.get('ATOM_AUTONOMOUS_CONFIG'), reason='Requires native camera fixture')
def test_randomized_starts_are_safe_varied_and_reproducible():
    from atom_mujoco.autonomous_env import AutonomousManipulationEnv
    config = json.loads(Path(os.environ['ATOM_AUTONOMOUS_CONFIG']).read_text())
    config['autonomous'] = {'reach_distance_squares': 1., 'start_radius_squares': [2., 3.]}
    env = AutonomousManipulationEnv(config, objective='reach', horizon=4)
    try:
        commands = []
        for seed in (7, 8, 9, 7):
            observation, info = env.reset(seed=seed)
            assert env.observation_space.contains(observation)
            assert info['pad_distance_m'] > info['reach_threshold_m']
            assert env.control.unexpected_contact() is None
            assert env.base.contact_guard.topple_event is None
            assert env.control.sweep(env.command, 1.)[0] is not None
            commands.append(env.command.copy())
        np.testing.assert_allclose(commands[0], commands[-1], atol=1e-12, rtol=0)
        assert not np.allclose(commands[0], commands[1])
        assert not np.allclose(commands[1], commands[2])
    finally:
        env.close()
