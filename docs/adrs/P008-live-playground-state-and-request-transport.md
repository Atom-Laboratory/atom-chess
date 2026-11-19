# P008 — Live Playground snapshots and square-only request transport

Date: 2026-11-05. Status: implementation in progress.

## Context

P006 provides a real Chess Core task adapter; P007 provides confirmed snapshots.
The existing GUI still supplies a piece ID and resets physics on every command.
That prevents sequences and discards failed or successful physical outcomes.

## Decision

Feedback follow-up: the adapter owns its monotonically increasing observation
sequence and samples snapshots itself. Callers cannot bind an old supplied
snapshot to fresh robot telemetry. Frame values are immutable Pose records.
These observations supply evidence only; P005 and P007 retain completion and
commit responsibilities. A failed sample does not consume a sequence number.

Use a versioned JSON MOVE envelope at the boundary and expose the same consumer
to headless execution and GUI controls. Add C++ serialization to the P006 adapter.
Scene initialization is explicit and separate from execution. Observe all piece
poses directly from MuJoCo and classify board occupancy by scene sites, support
height, upright orientation and settled velocity. Preserve identity across moves.

Drive P005 phase gates with measured simulation feedback and commit through P007
only after whole-board release verification. Failed operations require explicit
reconciliation; no automatic reset or replay. Simulation oracle evidence is
explicitly labeled. GUI selects source/target only. Compatibility piece IDs are
optional assertions, never authoritative identity.

## Alternatives

Copying the logical board into physical state bypasses verification. Resetting
per command hides disturbed pieces. Reimplementing chess move legality in Python
duplicates Chess Core. An in-process C++ binding introduces a packaging dependency;
versioned JSON allows a separately built producer and the existing Python runtime.

## Consequences

Geometry and feedback thresholds are explicit experimental configuration, not
measured CAD accuracy. This increment does not claim swept collision safety.
Graveyard transfers, full-plan serialization and collision validation follow in
separate increments. The transport consumes already planned tasks; it is not a
second chess engine and must never advance logical state on command submission.
Low-level position execution lives in a separate MotionController adapter. It
uses MuJoCo bias-force feedforward to compensate model gravity sag and verifies
measured joint settling with a timeout rather than assuming fixed-step success.
