# P015 trajectory playback

## Build and export

On Linux/WSL at the repository root:

    cmake -S . -B build/headless -DACCHESS_BUILD_VIEWER=OFF
    cmake --build build/headless --target export_mujoco_trajectory -j 4
    build/headless/software/integration/export_mujoco_trajectory > trajectory.json
    build/headless/software/integration/export_mujoco_trajectory --unreachable > rejected.json

The failure fixture intentionally exits 1. The exporter creates PhysicalTask,
calls MotionPlanner::planTask and runs the existing C++ IK for each waypoint.
It supports the experimental E2–E3 fixture. The current simulation lacks J3.
The position-only mapping and model-derived offsets are recorded in ADR P015.

## Execute in Windows

Use a fresh playground-graveyard-grid-v2 bundle with the existing board position.

    & ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/playground/run.py --bundle simulation/mujoco/assets/bundles/playground-graveyard-grid-v2 --headless --diagnostic-unchecked --execute-trajectory trajectory.json --output new-playback.json

For visible playback launch the Playground with -DiagnosticUnchecked and click
Execute C++ trajectory (P015). The ordinary MOVE buttons retain legacy Python
planning. The new playback path only validates and executes C++ targets.

COMPLETED_JOINT_PLAYBACK confirms target settling. The snapshot remains unchanged
and reconciliation is required before further task dispatch. Initial compatibility
uses [0.005 rad,0.006 m,0.005 rad,0.001 m,0.001 m] tolerances. Each target is checked
against the actual model using forward kinematics within 10 micrometres.
Settling uses 0.005 per arm coordinate and 0.001 m for open fingers. Closed phases
allow 0.006 m per finger, matching measured bilateral pawn contact at approximately
-0.01534 m for the -0.021 m command. Final opening uses the stricter tolerance.
Velocity must be below 0.01 per coordinate for ten consecutive control intervals.
Timeout is 600 control intervals per waypoint. The controller retains rate limiting
and gravity feedforward. Timing/acceleration profiles are absent from MotionPlanner.
The diagnostic opt-in bypasses swept preflight. Collision qualification, visual
confirmation and hardware mapping remain pending. The GUI is still synchronous.

## Tests

Set ATOM_P015_PLAN and ATOM_P015_REJECTED to the real exporter outputs, then run:

    & ./simulation/mujoco/.venv/Scripts/python.exe -m pytest simulation/mujoco/tests -q

The integration cases explicitly skip if these files are not configured. Playback
replaces legacy solve and execute with failing functions, compares every target
against the exported contract, and checks that the confirmed snapshot is identical.
Regressions cover malformed dimensions, units, frame, version, NaN/Inf, ordering,
missing fields, gripper commands, duplicate keys and planning/execution failures.

## Recorded evidence

The MotionPlanner CTest passed. The Python suite with real exporter outputs and rendering enabled passed 90 tests. The headless entry point completed all eight waypoints. Final Z error was 0.0000105023 m, arm hinge errors below 2e-15 rad and finger errors below 8e-12 m. The first contact run failed at GRASP_PIECE with a 5 mm closure allowance. After measuring the 5.66 mm contact-limited closure error, the diagnostic allowance was explicitly configured at 6 mm. The final opening still uses 1 mm. The interface was syntax-checked but interactive GUI playback has not been manually verified.
