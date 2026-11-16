# ADR-006: Validate the configured-branch IK contract

## Status

Accepted for numerical validation; complete solution search remains pending #153.

## Context

PR #178 fixes an inclusive inner-boundary rounding error. Issue #153 also asks
whether equivalent angles and the alternative elbow branch should be searched.
The current API explicitly selects one branch and has no previous joint state.
Silently changing branches can introduce discontinuities along a trajectory.

## Decision

Preserve configured-branch behavior while validating it with independent forward
kinematics, both elbow choices, joint/Z limits and singular boundaries. Include
explicit counterexamples for alternative-branch and equivalent-angle rejection.
Keep #153 open: passing these tests validates the existing contract, not complete
solution search or physical execution. Include the upstream #178 numerical fix.

## Alternatives

Automatic fallback would find more solutions but needs a trajectory continuity
policy. Normalizing every joint modulo 2 pi can violate cable/home-switch travel
semantics. Neither policy is introduced by this validation increment.

## Consequences

Tests are hardware independent and use synthetic dimensions. They establish
numerical XY/yaw consistency, not CAD accuracy, collision safety, reachability of
the physical chessboard or successful manipulation. Future branch selection must
define continuity and bounded angular travel before these limitations are removed.

## Recorded validation (2026-11-16)

The WSL/Linux `build/headless` build passed all 16 IK GoogleTests, including
120 forward/inverse round trips. CTest also passed the three selected targets:
`test_inverse_kinematics`, `test_motion_planner`, `test_motion_execution`.
An interrupted link initially left the execution-test binary invalid; rebuilding
that target resolved the infrastructure failure before the final passing run.
Stockfish was unavailable in this environment; no Stockfish or hardware test is
claimed. GCC/Clang matrix and repository-wide CI were not rerun by this increment.
