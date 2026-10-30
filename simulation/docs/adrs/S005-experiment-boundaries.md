# S005 — Direct MuJoCo experiments with explicit task decisions

Date: 2026-10-30. Status: accepted. Complements S003/S004 and L001.

## Context

The owner will implement learning personally. Main is integrated, but acmotion's
J1/J2/J3/Z/gripper contract exceeds this three-axis prototype. Measured TCP,
inertias, transmissions and robot collisions remain unavailable.

## Decision

Keep MuJoCo/NumPy direct Python APIs as the local CPU base. ROS is outside the
physics loop. Retain legacy Gazebo sources without adopting a second primary
simulator. Defer Gymnasium, PyTorch and SB3 installations until needed.

Allow explicit JSON overrides of synthetic mass/inertia, damping/armature,
position gains and timing. Each new bundle stores configuration and hashes.
Gravity/contact overrides are rejected until collision geometry/dynamics exist.
An optional experimental_tool offset in arm2_link supports tool-point FK study;
there is no invented default TCP. frame_pose returns world metres and rotation;
tool_pose is None without an offset, and tcp_calibrated stays false.

Episode requires a researcher Task and explicit max_steps. Task supplies reset,
observations, action conversion and reward/termination. Infrastructure handles
independent seeded streams, stepping, truncation and invalid targets. Errors after
physics mutation require reset. No default reward, policy or training exists.
This is not Gymnasium.Env; spaces and checker validation remain future work.

Local exclusive JSON records include code revision, dirty/untracked flags,
versions, manifest and wall time. Conventional demos leave task/algorithm/seed
null and document deterministic reset. Future task configuration/checkpoints must
be supplied by the researcher. Dirty/untracked sources are not auto-snapshotted.

## Alternatives and consequences

ROS on every step adds coupling without solving calibration; defer a bridge.
Premature Gymnasium spaces would silently choose experimental semantics; defer
formal compatibility. Local JSON suffices before introducing larger trackers.
The sphere/plane fixture checks engine contacts only, not robot collisions.
Manipulation and physical deployment remain blocked by mechanical evidence.
Validation: 25 pytest cases passed with rendering, including rigid tool transforms,
parameter rejection, episode reset/replay/termination, record preservation,
repository-wide provenance and Windows UTF-8 BOM input. No training was executed.
