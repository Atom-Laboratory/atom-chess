# P040 — Camera evidence for capture

## Context

P039 demonstrates physical execution in MuJoCo using simulator feedback. The
camera-guided capture must obtain its task evidence from RGB. Board ArUco
references currently establish the playing surface. Native piece candidates do
not establish a grasp pose, a held piece, or occupancy of an off-board slot.

## Decision

Add a separate capture inspection entry point. The acquisition adapter renders
RGB at an explicit observation pose. The evidence layer receives native camera
observations and task metadata. It reports candidate evidence and unavailable
requirements, and stops before motion while those requirements are unavailable.

A camera executor must establish a grasp pose, verify pickup and release, and
confirm the specified Graveyard slot before it authorizes the attacking move.
Use a measured visual reference for the Graveyard surface and qualify grasp
and release evidence against independent evaluation. Keep the P039
oracle-based exercise separately identified for simulation regression.


## Implemented fixed-fixture executor

run_camera_capture.py uses RGB-only gates after the arm returns to its
observation pose. It plans from fixed nominal square centers and checks an
independent scratch scene constructed from expected occupancy after RGB
acceptance. Live piece pose and contact feedback do not enter the executor
gates. The existing low-level MuJoCo controller still advances physics.
The fixed e4 to d5 fixture passed both transitions. Displaced-piece grasp
localization and visual identity or grip tracking remain outside this result.

## Camera-based XY for displaced pawns

The current executor obtains XY by matching images of known upright pawn
appearances against an explicit 1 mm calibration grid. Simulation renders
the calibration images from isolated scratch fixtures. Runtime matching takes
RGB only. Static support geometry supplies height. Placement acceptance
combines a region transition with the expected pawn appearance at the destination
after retreat. Two opposing ±2 mm offset configurations passed the complete
capture. This does not qualify tracking during motion or physical deployment.
