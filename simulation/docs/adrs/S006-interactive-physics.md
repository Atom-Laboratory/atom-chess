# S006 — Interactive control and experimental contact profile

Date: 2026-10-30. Status: accepted. Supersedes the default interactive entry point
in S005; preserves the previous diagnostic profile for reproducible exercises.

## Context and decision

The owner requested better reversible controls, gripper closing, collision,
gravity and visualization fixes. Add an explicit --interactive profile and make
the launcher use a new v4 bundle rather than altering old experiments.
Use a Tkinter control panel and native MuJoCo viewer, no new pip dependency.
Provide target sliders, +/- buttons, open/close, pause, reset, hold and camera
reset. Physics mutation uses the viewer lock; sync runs outside it.

Enable earth gravity and robot/environment contacts using separate convex mesh
hulls. Keep self-collision filtered until assembly contacts are reviewed.
Retain static pieces with collision instead of introducing untested free bodies.
Move the existing finger meshes with opposing parallel slides as an explicitly
synthetic mechanism. Do not apply the observed Fusion revolute limit to these
slides or pretend to have extracted the physical linkage.

Record profile assumptions in the manifest and document masses/gains/limits.
Keep v3 supported for three-axis exercises. The v4 state/target has five axes;
no hardware mapping or calibrated gripper/TCP is implied.

## Validation and limitations

28 pytest tests with rendering passed. Demo remained finite with no joint excess;
gravity creates about 5.1 mm steady Z error under the synthetic servo. Tests
verify reverse jogging, finger close/open/reopen, unsupported gravity descent
and real robot/environment contact reports. Native panel/viewer startup and
timed close passed; offscreen render was inspected. Windows console printing
was corrected to ASCII after its CP1252 encoding rejected a minus symbol.
No complete manual UI audit, physical grasp validation or self-collision
validation was performed. See the interactive controls guide for reproduction.
