# S012 — H-file camera references clear of the moving arm

## Context

P038 with the H-file camera lost its board reference during approach. The
previous marker 3 location was visible at reset but became occluded as the arm
moved. A successful static homography therefore did not qualify the motion.

## Decision

Use an experimental marker strip beyond the H-file edge. The single layout
source is simulation/mujoco/configs/perception/h-file-layout.json. The shared
camera remains defined in virtual_camera.py. Reference generation and fixture
preparation use that layout by default. Tests may supply --layout and
--camera-config and must preserve both resolved inputs in their run.

The four marker centers in rectified board millimetres are (330,-80),
(450,-80), (450,360), (330,360) for IDs 0 through 3. The board spans 0..280 mm
on both axes. u increases from file A towards H and v from rank 8 towards 1.
Black marker sides are 40 mm with a 4 mm white margin. Print with the orientation
and dictionary in the JSON. These are experimental simulation mounting positions
and require a physical support and measurement before hardware deployment.

## Alternatives and consequences

Moving a single marker retained occlusion during approach. The external strip
keeps the markers on the camera side of the arm. Its asymmetric placement
requires homography error checks over the entire board and trajectory.
The centered e4-to-d5 baseline completed all 92 steps with valid perception,
zero reported collisions and 0.185 mm simulated placement error. Native visual
placement confirmation remained false. The result qualifies this fixture's
board reference visibility, while manipulation reward uses simulator truth.

The wrist-capable automatic controller remains a separate pending migration.
This layout fix is tested against the existing five-actuator P038 environment.
