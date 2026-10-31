# S008 — Dynamic chess pieces and coupled gripper contacts

Date: 2026-10-30. Status: accepted. Supersedes v4 static-piece/independent-finger
behavior while preserving previously generated bundles.

## Problem

The owner observed finger misalignment and pieces that could not be lifted.
Pieces in v4 had no free joints, so they were anchored. Independent finger
targets permitted asymmetric commands. Convex hulls of complete CAD fingers
filled empty regions and were unsuitable as fingertip contact surfaces.

## Decision

Create interactive-chess-v5 with interactive-gravity-v2 profile. Move all 32
piece bodies from the board to world children with free joints, preserving
initial world poses. Use synthetic piece mass 0.02 kg and inertia diagonal
[0.000004, 0.000004, 0.000002] kg m². Enable piece/board, piece/robot and
piece/piece contacts. Reset restores both free bodies and controlled joints.

Couple the two opposed finger slides with a joint equality. Reject unequal
finger targets, and expose one shared opening slider in the control panel.
The equality is a soft physical constraint, not a CAD linkage reconstruction.
Replace finger convex hulls with localized box pads (half-sizes 0.015, 0.008,
0.003 m) at local [0.113,-0.009,0.105] and [0.113,-0.009,0.076] m. These are
explicit experimental contact proxies informed by mesh extents, not measured
rubber pads. Friction is synthetic (1.2 sliding, 0.01 torsional, 0.001 rolling).
Retain other robot convex collision approximations and self-collision filtering.

Separate controlled qpos/qvel addresses from free-body state: the model now has
229 qpos coordinates but only five actuators. Public robot observations remain
five-dimensional. No grasp attachment, weld, parenting change or policy is used.

## Validation and consequences

30 tests passed with rendering. A controlled fixture relocates other pieces,
places one pawn between the pads, then advances physics without any further
pose edits: close, lift 0.08 m, open and let gravity return the pawn to the board.
The test checks real pad contacts, finger agreement and reset of all piece states.
It does not establish reliable grasping among neighbors or a calibrated physical
gripper. Native v5 panel startup/close passed; offscreen rendering was inspected.
Generated v4 bundles remain available; the launcher selects a new v5 directory.
