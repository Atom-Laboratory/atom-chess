"""Verify invariants of the conventional servo, without training dependencies."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('kinematic_controller',
    Path(__file__).parents[1] / 'scripts/kinematic_controller.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def servo():
    return module.PositionServo((Path(__file__).parents[1] / 'urdf/atom.urdf.xacro').read_text())


def test_reordered_command_respects_speed_and_reaches_goal(servo):
    goals = [0.5, 0.1, 1.0]
    servo.command(servo.names[::-1], goals[::-1])
    for _ in range(40):
        before = servo.position.copy()
        servo.step(0.02)
        assert all(abs(q-old) <= speed*.02+1e-12 for q, old, speed in zip(servo.position, before, servo.speeds))
    assert servo.position == pytest.approx(goals)


@pytest.mark.parametrize('positions', [[0.0], [float('nan'), 0., 0.], [3., 0., 0.], [0., float('inf'), 0.]])
def test_invalid_command_is_atomic(servo, positions):
    before = servo.target.copy()
    with pytest.raises(ValueError):
        servo.command(servo.names, positions)
    assert servo.target == before


def test_duplicate_names_stop_and_reset(servo):
    with pytest.raises(ValueError):
        servo.command([servo.names[0]]*3, [0.]*3)
    servo.command(servo.names, [1., .1, 2.])
    servo.step(.02)
    servo.stop()
    held = servo.position.copy()
    servo.step(.1)
    assert servo.position == held
    servo.reset()
    assert servo.position == [0., 0., 0.]
    assert servo.target == servo.position


@pytest.mark.parametrize('dt', [0., -1., float('nan')])
def test_invalid_dt(servo, dt):
    with pytest.raises(ValueError):
        servo.step(dt)
