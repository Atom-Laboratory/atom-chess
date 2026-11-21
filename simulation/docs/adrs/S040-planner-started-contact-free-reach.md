# S040 — Planner-started contact-free reach experiments

Status: experimental. Date: 2026-11-20.

## Context

After S039, fixed-camera native approaches initialized on seeds 7/8 for isolated
and full-board fixtures. Existing version 7 remains an observation-only temporal
manipulation handoff, because grasp/lift workspace qualification is incomplete.
Version 6 reach weights were trained on screened randomized starts, not actual
planner endpoints. Treating their isolated success as integrated skill is wrong.

## Decision

Add a separate version 8 `native_reach` start mode, restricted to three-axis
`reach_xyz`, structured visual observations and the reach objective. Every reset
executes the native approach, checks tracking and fresh matching RGB, and starts
the actor from the issued endpoint command. No randomized robot teleport follows.
Keep wrist, elbow branch and fingers at the approach configuration. Require a
visible target during candidate screening. Use a declared task-space radius
around the visual XY and configured piece-top height; it is a proposal bound,
not an assertion that its entire volume is collision-free.

The canonical fixture's centered visible endpoint can lie outside that radius.
Permit an opt-in finite list (at most nine) of board-relative lateral entry
offsets, expressed in square pitches. All endpoints still come from native
planning/IK, pass the fixed-camera screen and conservative trajectory checks.
Offsets change the approach endpoint, never the visually estimated piece pose.
Candidate count remains bounded. This is an experimental search family, not
an adjustment of robot dimensions or camera geometry.

Every action must pass existing IK, velocity, bounds and complete swept checks.
Unlike manipulation, selected-piece pad contact is forbidden during this reach
experiment. Only the piece's existing support contact is exempted. Preserve
runtime contact, disturbance and camera-loss stops. Version 7 remains gated.
Neither mode grants a grasp/lift lease or confirms physical board occupancy.

Transfer from version 6 requires an explicit runner flag, configuration-transfer
consent, matching observation/action spaces and policy version, and archive hash
verification. Transfer initializes weights with a fresh optimizer; it is not a
resume or evidence that the old checkpoint solves this new start distribution.

## Alternatives and consequences

Continuing randomized-start PPO alone does not close the planner handoff gap.
Enabling seven-axis manipulation would bypass unresolved contact qualification.
The narrower reach experiment is measurable without doing either. First run a
deterministic camera/command-only reference from executed endpoints, then a
watched PPO smoke and held-out comparison. Do not train a grasp/lift policy based
on the resulting reach metrics. Sensor-only hardware deployment still requires
calibration and independent real outcome verification.
