# S021 — Gate approach strategy learning on physical feasibility

## Context

Bounded residual PPO did not approve a transfer from the full-board E2
fixture. The repeated first contact was between the gripper body and the
king on E1.

## Decision

Run an offline, bounded approach search using the existing robot geometry,
native IK, conservative sweep checker and low-level controller. Separate
kinematic screening, swept admission, dynamic grip and lift checks, and
RGB evidence. Record every tested candidate. The simulator oracle belongs
to the experiment evaluator. A future policy receives visual and host data.

## Alternatives

Longer residual training leaves the approach family unchanged. Arbitrarily
expanding action bounds gives exploration more ways to hit the board.
Physical or simulated collision geometry changes would confound this
comparison and require a separate model revision.

## Consequences

The search can reject proposed paths before executing them. Its finite grid
does not establish global infeasibility. A learned action interface and
recovery must be separately validated after the feasibility gate.
