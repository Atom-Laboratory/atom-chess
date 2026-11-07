# P006 — Square-only transfer boundary for Chess Core

Status: accepted for the first increment. Date: 2026-11-05.

## Context

ADR-003 defines `TaskPlanner` as the adapter from a validated Chess Core move
and its pre-move `Board` to ordered `PhysicalTask` values. Those values include
logical piece descriptors and physical coordinates in millimetres. Neither
identifies an observed object in the MuJoCo scene. P005 defines evidence-gated
execution. S010 and S011 describe a separate experimental Playground path.

## Decision

Adapt the complete C++ task plan at the integration boundary. For one ordinary
board transfer, emit a `BoardMoveRequest` containing canonical source and
target squares. Later execution resolves the source from a confirmed physical
snapshot. Reject empty plans, malformed endpoints and all plans outside the
supported single-transfer subset before any request is emitted. In particular,
never drop a capture-removal or promotion step from a plan.

## Alternatives

Passing the logical piece descriptor would require the caller to identify an
object that only physical observation can confirm. Rebuilding task decomposition
in Python would duplicate the existing special-move handling. Dispatching each
task as it is translated could execute part of an unsupported compound plan.

## Consequences

The adapter is transport-neutral and testable against the real TaskPlanner.
The consumer, physical snapshot and scene-specific geometry will follow in
separate increments. Existing graveyard reservations are still consumed during
planning. A caller must avoid reserving real slots for unsupported execution
backends until capability checks and reservation reconciliation are implemented.
