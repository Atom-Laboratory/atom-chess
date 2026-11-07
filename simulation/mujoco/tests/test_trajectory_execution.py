"""Run with ATOM_P015_PLAN pointing to the actual C++ exporter output."""
import json
import os
from pathlib import Path

import numpy as np
import pytest

from atom_mujoco.model import build_bundle
from atom_mujoco.playground import Playground
from atom_mujoco.trajectory_execution import PHASES, execute_trajectory, validate_trajectory


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    simulation = Path(__file__).resolve().parents[2]
    output = tmp_path_factory.mktemp("p015") / "bundle"
    build_bundle(simulation / "src/urdf/atom.urdf.xacro", output, interactive=True,
                 parameters={"board_center_m": [.28, .10, .012]})
    return output


@pytest.fixture
def plan():
    path = os.environ.get("ATOM_P015_PLAN")
    if not path:
        pytest.skip("Set ATOM_P015_PLAN to the output of export_mujoco_trajectory")
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.mark.parametrize("field,value", [
    ("schema", 2), ("units", ["rad"] * 5), ("frame", "robot_base"),
    ("joints", []), ("waypoints", []), ("status", "unknown"),
    ("initial", [0, float("nan"), 0, 0, 0]),
    ("initial", [0, float("inf"), 0, 0, 0]),
    ("initial", [0, .19, 0, 0, 0]),
    ("waypoints", None),
])
def test_invalid_contract_does_not_advance(bundle, plan, field, value):
    playground = Playground(bundle, diagnostic_unchecked=True)
    before = playground.sim.data.time
    plan[field] = value
    with pytest.raises(ValueError):
        execute_trajectory(playground, json.dumps(plan))
    assert playground.sim.data.time == before
    assert not playground.physical.reconciliation_required


def test_wrong_order_missing_fields_and_wrong_target(bundle, plan):
    playground = Playground(bundle, diagnostic_unchecked=True)
    before = playground.sim.data.time
    points = plan["waypoints"]
    points[0], points[1] = points[1], points[0]
    with pytest.raises(ValueError, match="phase order"):
        validate_trajectory(json.dumps(plan), playground.sim)
    points[0], points[1] = points[1], points[0]
    original = points[0].pop("xyz")
    with pytest.raises(ValueError, match="waypoint"):
        validate_trajectory(json.dumps(plan), playground.sim)
    points[0]["xyz"] = original
    points[0]["position"][2] += .1
    with pytest.raises(ValueError, match="forward kinematics"):
        validate_trajectory(json.dumps(plan), playground.sim)
    assert playground.sim.data.time == before


def test_real_cpp_playback_preserves_confirmed_snapshot(bundle, plan, monkeypatch):
    playground = Playground(bundle, diagnostic_unchecked=True)
    before = playground.physical.confirmed
    def forbidden(*args, **kwargs):
        pytest.fail("Legacy Python planning was invoked")
    monkeypatch.setattr(playground, "solve", forbidden)
    monkeypatch.setattr(playground, "execute", forbidden)
    result = execute_trajectory(playground, json.dumps(plan))
    assert result["status"] == "COMPLETED_JOINT_PLAYBACK", result["error_code"]
    assert [step["phase"] for step in result["history"]] == list(PHASES)
    for expected, actual in zip(plan["waypoints"], result["history"]):
        np.testing.assert_array_equal(actual["target"], expected["position"])
    assert playground.physical.confirmed is before
    assert playground.physical.reconciliation_required
    assert not result["collision_checked"]


def test_rejected_cpp_plan_does_not_advance(bundle):
    path = os.environ.get("ATOM_P015_REJECTED")
    if not path:
        pytest.skip("Set ATOM_P015_REJECTED to the exporter --unreachable output")
    playground = Playground(bundle, diagnostic_unchecked=True)
    before = playground.sim.data.time
    with pytest.raises(ValueError, match=r"C\+\+ planning failed"):
        execute_trajectory(playground, Path(path).read_text(encoding="utf-8"))
    assert playground.sim.data.time == before


def test_executor_error_is_not_success(bundle, plan, monkeypatch):
    playground = Playground(bundle, diagnostic_unchecked=True)
    before = playground.physical.confirmed
    def failed(target):
        raise RuntimeError("simulated actuator fault")
    monkeypatch.setattr(playground.controller, "step", failed)
    result = execute_trajectory(playground, json.dumps(plan))
    assert result["status"] == "FAILED"
    assert result["error_code"] == "simulated actuator fault"
    assert playground.physical.confirmed is before
    assert playground.physical.reconciliation_required


@pytest.mark.parametrize("fault", ["dimension", "nan", "infinity", "gripper", "missing", "duplicate"])
def test_waypoint_contract_rejection(bundle, plan, fault):
    playground = Playground(bundle, diagnostic_unchecked=True)
    if fault == "dimension":
        plan["waypoints"][0]["position"].pop()
    elif fault == "nan":
        plan["waypoints"][0]["position"][0] = float("nan")
    elif fault == "infinity":
        plan["waypoints"][0]["xyz"][0] = float("inf")
    elif fault == "gripper":
        plan["waypoints"][0]["position"][3:] = [-.01, -.01]
    elif fault == "missing":
        del plan["initial"]
    payload = json.dumps(plan)
    if fault == "duplicate":
        payload = payload.replace('"schema": 1', '"schema": 1, "schema": 1')
    with pytest.raises(ValueError):
        execute_trajectory(playground, payload)
    assert not playground.physical.reconciliation_required
