# P031 — Camera-based perception and sim-to-real RL architecture

Date: 2026-11-05. Status: **Proposed; Phase A only, awaiting architecture review.**

## Context

P020 already describes click-based chess validation. P023 introduced an isolated
pixel PPO experiment; P027–P030 add transfer learning and parallel visualization.
Those experiments do not implement camera-guided chess manipulation. The physical
system has one fixed oblique RGB camera. Firmware step counts and DONE events are
not measured joint positions. See [audit](../camera-rl/phase-a-audit.md).

## Decision proposed for review

Reuse the actual C++ acvision detector, Homography and PieceDetector. Start Phase B
with an offline executable linked to acvision: image plus explicit calibration in,
versioned observations and diagnostic images out. This enables reproducible image
tests without a camera device. Never substitute simulator poses for failed vision.
Keep RGB-to-BGR conversion in the acquisition boundary. Retain the original image
and rectify an undistorted copy using a versioned calibration and orientation.

Before high-throughput training, benchmark a persistent local executable against
a Python binding to the same C++ library. Prefer a binding if per-frame transport
is a significant bottleneck. Do not spawn a process or write PNG files per RL step.
There is no new distributed service or second implementation of perception.

Use a fixed elevated lateral camera opposite the player. Choose its experimental
extrinsics by coverage/occlusion measurements, not by assuming a measured physical
mount. Homography only maps the board plane. Board-to-base calibration is separate.
Height and visual gripper localization remain explicit missing capabilities.

Keep chess legality in acchess, task decomposition in the existing TaskPlanner,
main trajectories and constraints in acmotion, and execution in the controller.
The policy proposes bounded local corrections; the supervisor may reject them.
Commands and command-derived FK estimates must be labeled as estimates, not sensors.

Create a new environment, preserving VisualGraspEnv v3 and its checkpoints.
Separate PolicyObservation, SimulatorTruth, RewardEvaluator and EvaluationRecord.
The inference boundary receives only serialized/validated PolicyObservation and
returns a bounded action; it cannot receive an environment, simulator or callbacks.
Simulator reward/termination diagnostics must never enter policy features or
recurrent state. Real visual supervision and oracle evaluation remain distinct.

Start with structured visual observations where implemented and validated; compare
against a hybrid image representation. Occupancy alone is insufficient for local
grasp control. Neither structured 3D features nor grasp confidence may be fabricated.
No large training run until perception and a conventional manipulation baseline pass.

## Alternatives

- Retain local RGB PPO unchanged: preserves experimental results, but does not solve
  calibration, task conditioning, visual verification or deployment assumptions.
- Rewrite vision in Python: rejected because it creates two different perception paths.
- Bind acvision immediately: plausible final runtime, but first establish a stable
  output contract and test images; no throughput benefit is yet measured.
- RPC/microservices: unnecessary for local image processing and complicates timing.
- Structured-only policy: first candidate if localization becomes adequate; not
  currently possible from EMPTY/WHITE/BLACK alone.
- Full end-to-end chess RL: rejected; duplicates mature planning and chess logic.

## Consequences and gates

Phase B must first address board corner bias, orientation ambiguity, unknown cells,
calibration validity and RGB/BGR parity. A detected quadrilateral is not sufficient
evidence of a chessboard. Track image timestamps and reject stale perception.

Complete-motion visual verification, bounded residuals, collision checks, metric
calibration and held-out evaluation are prerequisites for later deployment claims.
Fingertip-only collision results do not qualify the full gripper or robot geometry.
Old weights are comparison artifacts, not automatically compatible warm starts.

Implementation phases, proposed contracts and acceptance evidence are in
[design and validation plan](../camera-rl/design-and-validation.md).
This ADR does not authorize advancing beyond the requested architecture review.
