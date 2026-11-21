# S042 — Screen local reach continuation before selecting an approach

Status: experimental. Date: 2026-11-20.

## Context

The S040 isolated approach-to-reach pilot passed, but the populated-board
reference stopped on a gripper hull/queen-D1 clearance check. The planner accepts
the first visible approach endpoint without asking whether a bounded local reach
can continue from that endpoint. A safe arrival is not a useful handoff by itself.

## Decision

Add an opt-in nominal reach-corridor screen to approach selection. From each
candidate endpoint, generate the same bounded XYZ direction proposals as the
deterministic reference, retaining that candidate's wrist, fingers and elbow
branch. Use RGB-estimated piece XY, calibrated board height and static piece
geometry. Verify each IK solution, model velocity limit, proposal bound and
complete nominal swept segment. Require the configured mean pad-gap threshold
within the actual episode horizon before choosing the approach candidate.

All planning probes run on scratch data reconstructed from camera estimates.
The rates are shared with the actual action decoder. Do not copy live piece
poses into the nominal screen or supply simulated coordinates to the actor.
Record rejected corridors and continue the existing bounded entry/wrist/branch
search. Keep the resulting corridor as planner diagnostic evidence, not as a
hidden policy input or an automatically executed grasp.

## Alternatives and consequences

Removing the queen or reducing clearance would change the task and is rejected.
Longer PPO training alone can waste rollouts at a bad arrival. Looking ahead
costs extra planning time but localizes failure before execution. This bounded
reference family is not a complete motion planner; rejection does not prove
physical impossibility. Runtime tracking, fresh RGB and per-action checks remain
mandatory. A nominal corridor does not qualify grasp, lift or hardware operation.
