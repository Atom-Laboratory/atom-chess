# P015 — MotionPlanner to MuJoCo Playground execution contract

## Audit and decision

MotionPlanner emits eight Cartesian Pose records in base-frame millimetres.
InverseKinematics returns JointTarget in radians, millimetres and gripper percent.
Neither produces timed segments, collision guarantees or velocity profiles.
The legacy Playground builds its own points and solves numeric IK. Its controller
and MuJoCo rate limiting are execution functions.

Use a versioned JSON file. The existing request adapter also uses JSON, and a file
lets Linux/WSL produce a reproducible plan for the Windows viewer without native
bindings, an IPC service or a Python extension build. The C++ exporter calls the
existing MotionPlanner and IK. Python validates the file, verifies model mapping
with forward kinematics, and sends the supplied targets through MotionController.

## Version 1

The experimental profile is tied to the current interactive v6 geometry.
The order is the exact five MuJoCo joint names. Positions use radians for hinges
and metres for slides. Cartesian targets are in MuJoCo world metres. Success
has eight ordered phase/position/xyz records and an initial joint configuration.
Failure has an operation ID and error with no waypoints. The last waypoint is
the final target. Timing, velocities, accelerations and tool-yaw control are
unavailable in this profile.

The fixture geometry was read from the loaded model at zero joints: shoulder
(40,0,35) mm, elbow (260,0,35) mm, and grasp center approximately
(372.83706,-90.32926,17) mm. The distal length is the norm of the elbow-to-TCP
XY offset. Its angle shifts the simulated J2 zero relative to the planar solver.
The Z target is relative to the zero-joint TCP. The two finger slides use the
existing experimental [-0.021,0] m interval and map aperture linearly. Both arm
hinges and the vertical slide have positive world Z axes. The hardware J3 solution
is outside this position-only simulation profile. Python checks Cartesian
positions of every target against the actual loaded model before motion.

## Execution and limits

The fixture produces an E2-to-E3 transfer for the current board. Grasp heights
are experimental and taken from the existing pawn demonstration. An explicit
diagnostic opt-in is required because P015 does not qualify collision clearance.
Execution reports joint settling, not successful manipulation. The confirmed
snapshot is preserved and the scene is marked for reconciliation before the first
command. Legacy square-based Python planning remains available separately.
