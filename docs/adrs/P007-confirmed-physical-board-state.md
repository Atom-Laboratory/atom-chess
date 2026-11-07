# P007 — Confirmed physical snapshots and transfer transactions

Date: 2026-11-05. Status: accepted for the state-contract increment.

## Context

P006 exposes square-only requests from the existing Chess Core TaskPlanner.
The Playground still resets each transfer and identifies pieces by their initial
square. P005 supplies phase evidence gates, but no authoritative physical snapshot.
Logical chess state cannot prove the location of a simulated or real object.

## Decision

Introduce a backend-neutral, in-memory physical state store in the existing Python
package. An immutable snapshot contains exactly 32 unique physical identities,
finite world-frame poses (metres, wxyz unit quaternions), and typed locations:
board square, named Graveyard slot, or gripper. Occupancy includes all 64 squares.
Slot names describe configured capacity, not invented Graveyard geometry.

Accept a square-only transfer against an explicit snapshot revision and resolve
its internal identity from occupancy. Serialize operations, reject occupied targets
(capture decomposition remains the upstream planner's responsibility), and record
pending/executing/completed/failed states. Keep live observations separate from
the last confirmed snapshot, including held-piece observations.

Commit only with the matching completed P005 execution and a fresh full snapshot
whose identity set, target occupancy and unaffected locations/poses agree. Require
explicit position and angular tolerances; these are adapter configuration, not CAD
measurements. Bind observations to the operation and require strictly increasing
observation sequence numbers. Any execution/verification failure preserves the
confirmed snapshot and blocks subsequent dispatch pending external reconciliation.

## Alternatives

Updating occupancy on dispatch invents success. Reusing Chess Core Board conflates
logical and physical truth. Parsing initial squares from piece names fails after
the first transfer. Automatically resetting physics hides partial failures.

## Consequences and limits

This increment is a tested state contract, not a simulator feedback adapter. P005
signals and supplied poses remain assertions of trusted adapters; this module does
not independently measure grasp, support or stability. It does not execute a stop.
Persistence, recovery/reconciliation workflow, scene pose classification, transport,
Playground wiring, actual Graveyard geometry and capture execution follow separately.
No RL training or collision-safety claim is enabled by this change.
