# S035 — Native approach as an episode start

## Context

The autonomous PPO environment initializes with a parked or sampled pose.
The approach qualification example already calls native `ac:motion` for
waypoints and IK, validates swept joint segments and executes them in MuJoCo.
Its arrival is measured independently of the command. It establishes a high
approach with an open gripper. Local descent and reliable lift remain open.

## Decision

Add an explicit `native_approach` start mode to the autonomous manipulation
environment. Reuse the existing approach planner and executor with retreat
disabled. Require successful execution, settled tracking, and a fresh
matching RGB reference with the target localized before building the
initial observation. Initialize from the issued command and fresh vision.
Keep measured joints, TCP, contacts and motion traces in diagnostics.

Use the temporal manipulation schema in this mode and record a distinct
environment version. The legacy reach profiles retain their original reset
semantics. Keep local policy actions gated in the M1 mode. The existing
workspace evidence and lease requirements still apply to future local
control integration. Record one reproducible result per seed and preserve
the failure stage, including failures that occur after motion.

## Alternatives

Replaying a pose from a prior report would bypass dynamics, the live swept
check and camera reacquisition. Reimplementing the waypoint generator would
split the training and simulation paths. Enabling grasp and lift immediately
would bypass the separate workspace and deterministic reference gates.

## Consequences

Resets include planning and physics execution time. A failed reset ends the
trial with a diagnostic and requires a new simulated reset. An admitted
observation means the approach and initialization passed for that fixture.
Full local workspace qualification, policy actuation, and hardware readiness
remain separate gates.
