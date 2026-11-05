# P009 — Graveyard endpoints and ordered composite execution

Date: 2026-11-05. Status: implementation in progress.

## Context

TaskPlanner already orders captured-piece removal before attacker movement. Its
allocator consumes calibrated XY positions during planning, while MuJoCo has no
Graveyard geometry. P008 only accepts one board transfer. Physical state must
retain a successfully removed piece even if a later transfer fails.

## Decision

Add explicit experimental Graveyard configuration to bundles: named slots with
world-frame centres and support surfaces. No dimensions are attributed to CAD.
Slots participate in physics, observed occupancy and destination resolution.
Generalize physical transfer endpoints to board squares or Graveyard slots while
keeping MOVE(source,target) as the public board-transfer operation.

Extend the C++ adapter with a complete ordered plan envelope. Map calibrated
removal targets to slot names through an explicit caller-provided resolver; never
reinterpret millimetres as scene metres. Reject unsupported promotion or malformed
plans before producing any request. Existing single-transfer schema stays valid.

Validate and reserve every destination against a projected occupancy snapshot
before execution. Serialize composite operations. Commit each verified transfer
individually; stop on failure and report partial completion. Reservations are
process-local and cannot be taken by another operation during execution. They do
not replace the upstream allocator's required transactional application handling.

## Alternatives and consequences

Inferring captures from chess rules in Python duplicates TaskPlanner. Removing a
piece by hiding or teleporting it does not demonstrate manipulation. Rolling back
the logical snapshot after physical removal invents a return transfer. Composite
results therefore expose completed steps and the last confirmed revision.

Named slots are transport-neutral. Their geometry is experimental and may be
unreachable with this prototype. Collision preflight and self-collision remain
the next mandatory increment before claiming safe generic execution. No RL is
enabled. Complete arbitrary chess positions require explicit physical inventory,
including captured pieces; promotion replacement remains unsupported hardware.
