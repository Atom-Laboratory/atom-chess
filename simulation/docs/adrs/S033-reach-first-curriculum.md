# S033 — Restart with bounded XYZ-only reach before grasp acquisition

## Context

The recovered seven-action comparison recorded approximately 3000 decisions
per branch without bilateral contact. Several episodes began 20–40 mm from
the piece and finished 100–300 mm away. Simultaneously learning XYZ, wrist,
finger travel, elbow branch and duration did not establish even reliable reach.
The operator requested a fresh, simpler progressive curriculum on 2026-11-10.

## Decision

Preserve old policies/results and stop their background session. Add an opt-in
environment version 4 `reach_xyz` profile to the existing autonomous runner.
Start fresh weights because three actions and their history differ from the
seven-action schema. Freeze wrist, elbow branch, open-finger command and action
duration. The policy proposes only XYZ increments, scaled explicitly by the
existing model-derived rates. Reject local workspace exits and disable silent
action projection in this profile. Keep all collision geometry/physics active.

Reuse existing RGB localization, observation construction, native IK, sweep,
feedback, PPO, Watch, CSV and checkpoint code. No hidden object pose enters the
actor. Use the existing geometric distance feedback for reach only; reaching
the declared neighborhood is not grasp or lift. The initial isolated stage
uses an explicit 0.5-square mean pad-clearance threshold, randomized checked
starts 1.25–2 squares from the visually localized source, fixed wrist zero,
elbow-down and a 2.5-square bounded local workspace. These are provisional
curriculum parameters, not hardware dimensions or a qualified manipulation
envelope. Pose initialization remains a simulation reset, not executed planning.

Evaluate a bounded pilot on separate seeds before longer training or escalation.
Then qualify reach with neighbors, acquisition of stable bilateral grasp, lift,
and planned transport/placement as separate stages. Do not reduce collision
clearance, relabel reach as manipulation, or automatically advance on training
reward. The intended deployment keeps global travel with MotionPlanner; this
isolated reach profile tests the local skill prerequisite, not that integration.

The first version-4 1024-decision pilot scored 0/8 before and after, with median
best gap improving from 33.13 to 31.34 mm. A camera/static-geometry reference
controller reached the same threshold in 2/2 checked episodes. Thus the target
is feasible, but learning has not passed. Introduce an explicit version-5
`dense_progress_v2` reward profile: multiply signed geometric progress by 10
and set the extra time-limit penalty to zero. Keep step cost, collision/failure
and toppling penalties unchanged. A time-limit truncation is not physical
failure. These are recorded training hyperparameters, not physical tolerances.
Keep version-4 configs/checkpoints distinct and restart the new pilot fresh.

The version-5 2048-decision pilot recorded one training reach but still 0/8
evaluation successes and essentially unchanged median gap (33.108 mm). The
deterministic policy's near-zero actions confirm a learning limitation, not
just viewer scale. Add an explicit version-6 `vision_features_v1` observation
profile for reach: use native camera-derived source position relative to issued
FK and a static model-height approach candidate, plus task/command context.
Normalize relative values by the declared local workspace. Exclude raw RGB and
image/command history from the actor dictionary in this profile; continue
capturing/processing the real RGB frames through ac:vision. Reuse the existing
feature extractor's vector path (small MLP, no NatureCNN). No simulator piece
pose is used for the relative target. This is a structured-vision ablation,
not a second sensor or a claim that raw-pixel manipulation is solved. Restart
fresh because input spaces/architecture differ and compare before/after again.

## Alternatives and consequences

More hours of unchanged free exploration would preserve the observed wandering.
Warm-starting an incompatible seven-action head would conceal changed semantics.
Removing hulls or neighbors without identifying a new fixture would change the
task silently. Add action/observation/version, fixed-control, workspace and
native integration tests. Keep old default behavior unchanged for comparison.
