from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def sweep(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'training/camera-manipulation'))
    import approach_sweep
    return approach_sweep


def test_grid_contains_all_entry_directions_and_stays_inside_wrist_travel(sweep):
    env = SimpleNamespace(residual_bounds=(.002, .002, .00225, .001),
                          motion=SimpleNamespace(default_wrist=np.pi/5),
                          sim=SimpleNamespace(lower=[0.], upper=[2*np.pi]))
    options = list(sweep.strategies(env))
    assert len(options) == len(set(options))
    assert all(0 <= option.wrist_deg <= 360 for option in options)
    assert {option.entry_xy_m for option in options[:312]} == {
        (0., 0.), (.008, 0.), (-.008, 0.), (0., .008), (0., -.008)}


def test_selected_wrist_and_offset_persist_across_pick_and_lift(sweep):
    solve = lambda xyz, opening, wrist: np.array([*xyz, opening, wrist])
    env = SimpleNamespace(source=np.array([.2, -.1, 0.]), pick_z=.03, safe_z=.10,
                          piece_height=.04, aperture=-.01, grasp=-.015,
                          motion=SimpleNamespace(solve=solve),
                          sim=SimpleNamespace(validate=lambda command: command))
    result = sweep.waypoints(env, sweep.Strategy(150., (.008, 0.), (.002, 0.), .00225, 0.))
    assert [phase for phase, _ in result] == ['approach', 'descend', 'align', 'close', 'lift']
    assert all(np.isclose(command[-1], np.radians(150)) for _, command in result)
    assert result[1][1][0] == pytest.approx(.210)
    assert result[2][1][0] == pytest.approx(.202)
    assert result[-1][1][2] > result[-2][1][2]


def test_preflight_scene_does_not_copy_hidden_piece_state(sweep):
    model = SimpleNamespace(qpos0=np.array([0., .25, -.10, .02]),
                            body=lambda _: SimpleNamespace(id=0),
                            body_jntadr=[0], jnt_qposadr=[1])
    scene = sweep.PickupSweep.__new__(sweep.PickupSweep)
    scene.env = SimpleNamespace(observed_offsets={'e2': [.001, -.002]}, occupied={'e2'})
    scene.model = model
    scene.sim = SimpleNamespace(qadr=[0], manifest={'pieces': [{'name': 'pawn', 'initial_square': 'e2'}]},
                                data=SimpleNamespace(qpos=np.array([7., 9., 12., 15.])))
    scene.park = np.array([.5])
    scene.checker = SimpleNamespace(initial=np.empty(4))
    scene.visual_scene()
    first = scene.checker.initial.copy()
    scene.sim.data.qpos[:] = -25.
    scene.visual_scene()
    np.testing.assert_array_equal(scene.checker.initial, first)
    np.testing.assert_allclose(first, [.5, .251, -.102, .02])
    scene.env.observed_offsets = {}
    with pytest.raises(ValueError, match='Incomplete RGB localization'):
        scene.visual_scene()
