# ADR-002: acmotion boundaries and SBC/ESP32 responsibility split

## Status

Proposed for the acmotion integration chain (#152, #155, #156).

## Context

ATOM Chess is distributed across Linux SBCs and an ESP32-S3. The motion stack must remain testable on Linux without robot hardware while preserving deterministic low-level control on the microcontroller.

Mixing chess semantics, Cartesian planning, inverse kinematics and STEP/DIR control in the same runtime would increase coupling, make hardware testing harder and complicate fault recovery.

## Decision

Split motion responsibilities at the joint-space execution boundary.

### Linux SBC / Brain

The SBC owns:
- `TaskPlanner`;
- `CoordinateMapper`;
- `GraveyardAllocator`;
- `MotionPlanner`;
- Cartesian `Pose` generation;
- inverse kinematics;
- `JointSegment` construction;
- `MotionExecution`;
- protocol sequencing, timeout and high-level recovery decisions.

### ESP32-S3

The ESP32-S3 owns:
- ACM1 command parsing;
- segment buffering;
- interpolation;
- velocity/acceleration motion profiles;
- conversion from joint targets to STEP/DIR;
- motor synchronization;
- Z-axis and gripper low-level actuation;
- endstop / limit input;
- emergency-stop handling;
- ACK / DONE / ERR / ESTOP / LIMIT responses.

### Boundary rule

The firmware must not depend on:
- FEN;
- `Board`;
- `Move`;
- `PieceType`;
- chess `Square`;
- graveyard allocation policy;
- Cartesian inverse-kinematics decisions.

The host must not generate individual STEP pulses or directly encode DRV8825 timing policy.

## Consequences

The Linux motion core can be unit-tested without hardware.

The ESP32 firmware can be tested against joint-space protocol fixtures without linking chess or computer-vision code.

Physical integration becomes a contract test between `JointSegment` and the firmware rather than an implicit coupling between modules.

Changing the manipulator geometry requires updating SBC-side configuration and IK, not chess-domain or firmware semantics.

## Integration checks

Before connecting motors:
1. verify host build/tests;
2. verify coordinate-frame conventions;
3. verify IK with measured dimensions;
4. verify protocol over serial with motor power disabled;
5. verify endstop/E-stop responses;
6. only then enable drivers and perform low-speed joint tests.

## Related

- #56
- #58
- #152
- #153 / #156
- #154 / #155
