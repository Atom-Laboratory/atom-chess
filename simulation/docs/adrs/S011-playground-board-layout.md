# S011 — Explicit experimental board placement for the Playground

Date: 2026-11-05. Status: accepted for simulation.

E2 in the original v6 scene is 452.55 mm from J1. The planar reach bound
is 364.54 mm. The Playground launcher builds a separate bundle using the
versioned `playground/configs/playground-board.json` scene parameter. The board center
is [0.28, 0.10, 0.012] m in the scene frame. The builder applies the placement
to the board, square sites and initial piece positions and records it in the
manifest. This layout was selected by simulation trials. Physical board
placement and reachability of all 64 squares remain unverified.

Set the pawn grip waypoint 18 mm above its simulated origin. The previous
23 mm waypoint failed to retain the pawn during lift in this layout. The new
regression exercises the standard opening position and verifies a physical
grasp, lift, transfer and release at E3 using MuJoCo state. Independent visual
confirmation remains a separate acceptance requirement. The ordinary view and
demo modes continue to use the original v6 layout.
