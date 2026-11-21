# S046 — Include the verified lateral entry in the deterministic diagnostic

Status: experimental; no policy admission. Date: 2026-11-21.

## Context

The crowded reach planner now uses a checked lateral entry. The old M4 grasp
diagnostic declares XY bounds only half a square around the source, which can
exclude the actual lateral approach endpoint. That rejects the first diagnostic
proposal before testing physical grasp behavior.

## Decision

Declare the diagnostic XY box as the union of the existing source neighborhood
and the verified entry position plus one diagnostic control interval of travel.
Use only the signed plan, camera-estimated source and static model rates. Keep
Z, finger and joint bounds, complete path/step collision checking, tracking and
runtime fault handling. The wider numeric box is not a collision-free certificate.

## Alternatives and consequences

Teleporting the gripper to the center or skipping bounds checks would bypass the
executed handoff. A diagnostic bound that actually includes its verified start
allows a meaningful controlled test without doing either. Test grasp and lift
under the existing deterministic supervisor before extending learned actions.
Keep `training_eligible=false` and visual verification unqualified; simulator
contact evidence alone must not grant a camera-only hardware manipulation lease.
