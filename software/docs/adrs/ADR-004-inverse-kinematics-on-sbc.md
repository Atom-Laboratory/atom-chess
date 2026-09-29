# ADR-004: Inverse kinematics runs on the Linux SBC

## Status

Proposed for #153 / PR #156.

## Context

The SCARA manipulator requires conversion from Cartesian end-effector poses into joint-space targets before low-level execution.

Placing inverse kinematics in the ESP32 firmware would couple manipulator geometry, frame conventions and workspace policy to the embedded controller. That would make simulation, numerical testing and future geometry changes harder.

## Decision

Run inverse kinematics on the Linux SBC / Brain.

The SBC converts:

```
Pose(x, y, z, gripper)
    ↓
InverseKinematics
    ↓
JointTarget(theta1, theta2, z, gripper)
```

The ESP32-S3 receives joint-space targets only.

### Geometry

The solver is parameterized by:
- link 1 length in millimetres;
- link 2 length in millimetres;
- joint 1 angular limits in radians;
- joint 2 angular limits in radians;
- Z travel limits in millimetres;
- deterministic elbow configuration.

No project-specific physical dimensions are hard-coded in the solver.

### Model

The planar 2R solution uses:

```
c2 = (x² + y² - L1² - L2²) / (2 L1 L2)
theta2 = ±acos(c2)
theta1 = atan2(y, x) - atan2(L2 sin(theta2), L1 + L2 cos(theta2))
```

The selected elbow branch is explicit and deterministic.

## Coordinate-frame assumptions

Before physical use, the team must document and measure:
- SCARA base origin;
- positive X direction;
- positive Y direction;
- positive joint rotation conventions;
- zero/reference angle of each revolute joint;
- positive Z direction;
- tool-center-point offset, if any;
- board plane height relative to Z zero.

These values are hardware configuration, not implementation constants.

## Consequences

IK is testable numerically without the robot.

Manipulator geometry can change without modifying firmware protocol semantics.

The firmware remains simpler and deterministic.

Incorrect frame definitions or CAD measurements can still produce physically unsafe targets, so integration must begin with motor power disabled and then progress through low-speed joint validation.

## Physical validation sequence

1. Measure L1/L2 and joint zero references.
2. Record mechanical joint and Z limits.
3. Validate solver against hand-computed/reference points.
4. With motors disabled, compare generated targets against expected joint values.
5. Enable one axis at low speed.
6. Validate both revolute axes independently.
7. Validate combined planar moves.
8. Validate Z.
9. Only then test full Cartesian pick-and-place trajectories.

## Related

- #56
- #58
- #153
- #156


## Joint 3 extension required for the selected arm

The current solver is planar 2R position IK. Dejan's How To Mechatronics SCARA includes a third revolute joint at the distal arm/end-effector in addition to J1/J2 and Z.

For ATOM Chess, #160 must define an explicit planar end-effector orientation contract. A likely MVP policy is to solve J1/J2 for XY and compute J3 to maintain a fixed tool/camera orientation relative to the board. This decision must be implemented and tested before autonomous powered motion.
