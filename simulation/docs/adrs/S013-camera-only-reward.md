# S013 — Experimental camera-only reward mode

## Context

P038 actor observations use RGB, but its original reward evaluator reads piece
poses, contact state and velocities. A camera-only experiment must have an
explicitly different reward and termination contract.

## Decision

Add --camera-only to the canonical camera-manipulation launcher. CameraOnlyEnv
uses the existing nominal planner and bounded residual actions. It obtains task
reward and success exclusively from temporally consistent native acvision
source-absence and destination-presence candidates during retreat. Initial
source presence is required. Grasp and collision truth metrics are unavailable.

The environment uses a synthetic empty-board RGB calibration in a separate
scratch state. Static robot and board geometry supplies nominal trajectories.
Host command history supplies phase progression. Runtime piece positions,
velocities and contact feedback do not supply reward or termination.

## Consequences

This experiment remains a five-actuator residual policy. A single board camera
does not establish bilateral contact, lift height, uprightness or release.
Visual success is candidate evidence. Collision safety qualification is pending
for this mode because it omits the original privileged moving-piece supervisor.
The original reward mode remains available for historical evaluation.

A new policy is required for the changed reward contract. This mode does not
resume an oracle-reward run. Preserve configuration, checkpoint, report and
camera evidence in the same experiment directory.
