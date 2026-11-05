# P019 — Board layout within the current gripper workspace

## Decision

Use an explicit experimental board layout centered at world [0.245,0,0.012] m
with 0.035 m squares. Preserve the existing arm geometry. The previous 0.04 m
layout extended past the current TCP workspace. Board size is now a validated
bundle parameter rather than an implicit global constant. The launcher creates
playground-reachable-board-v1 and retains prior bundles.

## Evidence and consequences

All 64 square centres passed numerical IK at world Z=0.031 m and 0.101 m,
covering pawn grasp and approach heights. These 128 tests establish nominal
kinematic reach within the joint limits. Full collision-free approaches in the
populated board still need validation. Official knight width is approximately
32.75 mm, leaving limited clearance in a 35 mm square. Other piece heights and
gripper orientations require their own tests. Graveyard supports remain 2x8 per
color outside the board and are not covered by the 64-square reach result.
The board dimensions are a simulation fixture, not the measured future board.
P015 exported trajectories from older layouts require regeneration for this scene.
