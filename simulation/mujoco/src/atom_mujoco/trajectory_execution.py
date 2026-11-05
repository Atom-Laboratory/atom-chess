"""Validate and execute a C++-planned trajectory without solving IK."""
import json
import math

import mujoco
import numpy as np


JOINTS = ["joint_base_to_link1", "joint_z_axis_arm1",
          "joint_arm1_link_arm2_link", "finger_1", "finger_2"]
UNITS = ["rad", "m", "rad", "m", "m"]
PHASES = ("APPROACH_SOURCE", "LOWER_TO_SOURCE", "GRASP_PIECE", "LIFT_PIECE",
          "APPROACH_TARGET", "LOWER_TO_TARGET", "RELEASE_PIECE", "RETRACT")
INITIAL_TOLERANCE = np.array([.005, .006, .005, .001, .001])
FINAL_TOLERANCE = np.array([.005, .005, .005, .001, .001])


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def _vector(value, size):
    if not isinstance(value, list) or len(value) != size or any(
            type(n) not in (float, int) or not math.isfinite(n) for n in value):
        raise ValueError(f"Expected {size} finite numeric components")
    return np.asarray(value, dtype=float)


def validate_trajectory(payload, sim):
    document = json.loads(payload, object_pairs_hook=_unique_object)
    if (not isinstance(document, dict) or type(document.get("schema")) is not int
            or document["schema"] != 1 or not isinstance(document.get("operation_id"), str)
            or not document["operation_id"].strip()):
        raise ValueError("Unsupported trajectory envelope")
    if document.get("status") == "failed":
        if set(document) != {"schema", "operation_id", "status", "error"} or not isinstance(
                document["error"], str) or not document["error"].strip():
            raise ValueError("Malformed planning failure")
        raise ValueError(f"C++ planning failed: {document['error']}")
    if set(document) != {"schema", "operation_id", "status", "profile", "frame",
                          "joints", "units", "initial", "waypoints"}:
        raise ValueError("Unexpected or missing trajectory fields")
    if (document["status"] != "planned" or document["profile"] != "atom-v6-position-only"
            or document["frame"] != "mujoco_world" or document["units"] != UNITS):
        raise ValueError("Incompatible planning status, profile, frame or units")
    if document["joints"] != JOINTS or list(sim.names) != JOINTS:
        raise ValueError("Incompatible joint order")
    if (sim.model.nu != len(JOINTS)
            or not np.array_equal(sim.model.actuator_trnid[:, 0], sim.joint_ids)
            or not all(sim.model.actuator(i).name == name + "_position"
                       for i, name in enumerate(JOINTS))):
        raise ValueError("Incompatible actuator mapping")

    def position(values):
        target = sim.validate(_vector(values, len(JOINTS)))
        if not np.allclose(target[3:], target[3], atol=1e-12, rtol=0):
            raise ValueError("Finger slide targets must agree")
        return target

    initial = position(document["initial"])
    if np.any(np.abs(sim.observe()["position"] - initial) > INITIAL_TOLERANCE):
        raise ValueError("Scene does not match the planned initial configuration")
    waypoints = document["waypoints"]
    if not isinstance(waypoints, list) or len(waypoints) != len(PHASES):
        raise ValueError("Expected the complete eight-waypoint sequence")
    scratch = mujoco.MjData(sim.model)
    scratch.qpos[:] = sim.data.qpos
    targets = []
    for phase, waypoint in zip(PHASES, waypoints):
        if (not isinstance(waypoint, dict) or set(waypoint) != {"phase", "position", "xyz"}
                or waypoint["phase"] != phase):
            raise ValueError("Invalid waypoint or phase order")
        target = position(waypoint["position"])
        if target[3] != (sim.lower[3] if phase in PHASES[2:6] else sim.upper[3]):
            raise ValueError("Unexpected gripper target for phase")
        xyz = _vector(waypoint["xyz"], 3)
        scratch.qpos[sim.qadr] = target
        mujoco.mj_forward(sim.model, scratch)
        if np.linalg.norm(scratch.site("grasp_center").xpos - xyz) > 1e-5:
            raise ValueError("Cartesian waypoint is inconsistent with MuJoCo forward kinematics")
        targets.append((phase, target))
    return document["operation_id"], targets


def execute_trajectory(playground, payload):
    if not playground.diagnostic_unchecked:
        raise ValueError("P015 playback requires explicit diagnostic mode")
    if (playground.manual.active or playground.manual.stopped
            or playground.physical.reconciliation_required
            or any(op.status in ("pending", "executing")
                   for op in playground.physical.operations.values())):
        raise ValueError("Trajectory playback requires an idle, reconciled scene")
    sim = playground.sim
    operation, targets = validate_trajectory(payload, sim)
    playground.physical.invalidate()
    history = []
    result = dict(schema=1, operation_id=operation, planner="cpp_motionplanner",
                  status="FAILED", collision_checked=False, training_eligible=False,
                  verification="simulated_joint_targets", history=history,
                  physical_revision=playground.physical.confirmed.revision,
                  reconciliation_required=True, error_code=None)
    try:
        for phase, target in targets:
            tolerance = FINAL_TOLERANCE.copy()
            if phase in PHASES[2:6]:
                tolerance[3:] = .006  # Pad contact can limit the commanded closure.
            settled = 0
            for _ in range(600):
                state = playground.controller.step(target)
                error = np.abs(state["position"] - target)
                if playground.on_step:
                    playground.on_step(phase, state)
                if np.all(error <= tolerance) and np.max(np.abs(state["velocity"])) <= .01:
                    settled += 1
                    if settled >= 10:
                        break
                else:
                    settled = 0
            else:
                raise RuntimeError(f"JOINT_TARGET_NOT_SETTLED: {phase}")
            history.append(dict(phase=phase, target=target.tolist(),
                                measured=state["position"].tolist(), abs_error=error.tolist()))
        result["status"] = "COMPLETED_JOINT_PLAYBACK"
    except (ValueError, RuntimeError) as error:
        result["error_code"] = str(error)
    return result
