# S010 — Bounded MuJoCo wrist rotation

## Context

The physical gripper rotates about the arm mounting axis through one revolution
and uses a switch for homing. The interactive model previously fixed the
gripper back and finger slides to arm2. Five-actuator task and policy inputs
encode that geometry.

## Decision

Add an opt-in six-actuator manual simulation profile. Fit circles to the
exported gripper_back.stl flange and arm2.stl mounting ring in the assembly XZ
plane. Both give X=372.837 mm and Z=90.329 mm. Apply the existing -260 mm
mesh X offset to place the hinge in arm2. The local Y axis maps to world Z
in the upright model. The hinge position uses the flange plane at Y=133.398 mm.
Parent the gripper back, finger slides, contact pads and grasp site to this
hinge. Keep the finger command indices and append the wrist command.

Use a limited [0, 2*pi] position target. Zero is the exported mesh pose and the
simulation home convention. The actual switch angle, motor sign and speed
still require hardware calibration. The hinge does not wrap through its ends.

## Alternatives and consequences

A continuous hinge would permit travel past the one-turn constraint. Changing
the existing model by default would invalidate five-actuator trajectories and
checkpoints. The separate bundle lets developers exercise the sixth axis and
its tip contacts before migrating planner, capture and policy schemas.
