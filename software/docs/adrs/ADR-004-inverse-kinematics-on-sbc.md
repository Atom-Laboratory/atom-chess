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
Pose(x, y, z, gripper, toolYaw)
    ↓
InverseKinematics
    ↓
JointTarget(theta1, theta2, theta3, z, gripper)
```

The ESP32-S3 receives joint-space targets only.

### Geometry

The solver is parameterized by:
- link 1 length in millimetres;
- link 2 length in millimetres;
- joint 1 angular limits in radians;
- joint 2 angular limits in radians;
- joint 3 angular limits in radians;
- joint 3 zero offset in radians;
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

For the distal axis:

```
theta3 = toolYaw - theta1 - theta2 - joint3ZeroOffset
```

This keeps the planar end-effector/camera orientation explicit and independent from the J1/J2 position solution.

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


## Joint 3 orientation policy for the selected arm

The selected How To Mechatronics SCARA includes a third revolute joint at the distal arm/end-effector. ATOM therefore treats tool yaw as part of the Cartesian pose.

J1/J2 solve XY position. J3 compensates the accumulated J1/J2 rotation so the requested tool/camera yaw is maintained relative to the SCARA base frame.

The physical zero offset and J3 limits remain calibration data, not hard-coded geometry.
