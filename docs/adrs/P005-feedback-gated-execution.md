# P005 — Persistent task identity and evidence-gated execution

Date: 2026-11-05. Status: accepted incremental implementation.

Implement transport-independent supervision in the existing Python simulation
package to exercise protocol semantics before attaching hardware. SQLite provides
persistent task IDs and atomic claim, avoiding physical dispatch on duplicate or
restart. Same-ID changed payloads are errors. Freshness/source/sequence/board
revision and explicit signal sets are checked at every phase transition.

Default execution rejects simulation oracle evidence. Tests may enable oracle
explicitly; this does not turn simulation truth into a real sensor. Sensor adapters
and confidence/dwell fusion remain pending. A claimed signal from an arbitrary
caller is not authenticated proof. Controller ACK does not confirm a grasp.

Without verified stop/recovery transport, fault handling fails with intervention
required rather than executing an unvalidated recovery movement. ABORTED describes
orchestrator state, not confirmed physical stop. Polling must be externally driven;
this library is not a hardware watchdog or safety certification.

Add a seeded local joint-tracking baseline with per-axis metrics and model/code
provenance. Do not label it a learned manipulation benchmark. Five seed-7 trials
executed on the workstation; full manipulation/generalization/embedded benchmarks
remain pending. Physical validation blocks later hardware phases; model uncertainty
is not repaired by adding training or randomization before validating mechanics.

Tests cover ordered success gates, stale/future/oracle rejection, board conflict,
duplicate identity, changed-payload conflict, persistent terminal status, cancel
idempotence and timeout. No motors, policies or Chess Core state are modified.
