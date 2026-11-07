# Physical state developer guide

This implements [P007](../adrs/P007-confirmed-physical-board-state.md). It is a
backend-neutral state contract in `atom_mujoco.physical_state`, now consumed by
the [live Playground adapter](playground-integration-guide.md).
The tests use synthetic snapshots and supplied oracle assertions, not physical
manipulation evidence. Do not use them to claim successful captures or safety.

## Responsibility and data

Chess Core validates chess moves. The C++ P006 adapter emits source/target squares.
The physical state store resolves the internal piece identity. Neither callers
nor the adapter need to infer identity from a logical piece type or initial name.

Each `Snapshot` has a revision, exactly 32 unique `Piece` records and a configured
set of Graveyard slot names. Each piece has a world-frame `Pose` (metres and wxyz
unit quaternion) and one `Location`: board square, Graveyard slot or gripper.
All 64 squares appear in `snapshot.occupancy`, with `None` for empty squares.
Captured pieces remain in the inventory. Location uniqueness prevents two pieces
from sharing a square/slot or occupying the single gripper simultaneously.

Snapshots are immutable. `store.confirmed` is the last confirmed state;
`store.observation` is separate live evidence and may show a piece held in transit.
The confirmed state can therefore intentionally lag physics during execution.

## Adapter implementation steps

1. Explicitly initialize and settle the scene. Observe all 32 objects. Transform
   poses into a documented common frame and classify their physical locations
   from configured geometry. Reject ambiguous observations. Supply a `Snapshot`;
   do not derive live occupancy from initial-square suffixes in mesh names.
2. Construct `PhysicalBoardState(snapshot, position_tolerance_m=...,
   angle_tolerance_rad=...)` with documented measurement tolerances. This module
   does not provide guessed defaults or validate the geometric classification.
3. Call `request_move(source, target, operation_id=...,
   expected_revision=store.confirmed.revision, timeout_s=...)`. The return value
   is the existing P005 `MoveTask`, with the internally resolved piece identity.
   The operation is pending. Only one operation may be active.
4. Call `start(task.task_id)` when dispatch begins. Construct the P005 `Execution`
   with that exact task and a `TaskLedger`. Drive its evidence gates from real
   backend observations; use `allow_oracle=True` only for explicitly identified
   simulation testing. An ACK alone does not complete those gates.
5. During execution, submit `Observation(task.task_id, sequence, timestamp_s,
   snapshot)` through `observe`. Sequence numbers increase across the lifetime of
   the store. Snapshot revisions remain the operation's starting revision.
   Timestamps use the same clock as P005 execution. Observation does not commit.
6. After P005 reaches `COMPLETED`, collect a fresh full post-release snapshot.
   Call `commit(task.task_id, execution, now_s=...)`. The store checks the matching
   task, completion, freshness, inventory, destination location and unaffected
   pieces' locations/poses. A successful commit increments the revision once.
7. On execution failure call `fail(task.task_id, reason)`. Commit verification
   failures do this automatically. The last confirmed snapshot remains unchanged;
   the store rejects further dispatch. Request controller stop separately and
   verify it. No stop IO or recovery motion is implemented here.

The adapter remains responsible for truthful support, release, grip stability,
pose-to-square classification and full swept collision checks. Setting a location
field or supplying a P005 signal is not an independent physical measurement.

## Failure, captures and restart

Inspect `operations` for pending/executing/completed/failed status and failure
detail, and compare `observation` with `confirmed` to diagnose uncertainty.
Do not reset the scene or create a fresh store to silently clear a failed move.
Recovery requires an externally verified full-state reconciliation workflow,
which is not implemented in this increment.

Occupied destinations are rejected. The existing upstream capture planner must
first remove the captured object; Graveyard endpoint transfers and transactional
slot reservations are a later increment. Slot records alone do not create
simulated geometry or collision obstacles.

This store is single-owner and in-memory. Serialize access. P005 has a persistent
ledger, but physical snapshot persistence and atomic ledger/snapshot commits are
not implemented. After process restart, reconstruct state through observation and
reconciliation; do not replay an in-progress operation automatically.

## Run the regression checks

From the checkout root in Windows PowerShell:

```powershell
& ./simulation/mujoco/.venv/Scripts/python.exe -m pytest simulation/mujoco/tests/test_physical_state.py simulation/mujoco/tests/test_supervision.py -v
```

Coverage includes square-only resolution, two successive committed transfers,
held observations, Graveyard inventory, immutable occupancy, malformed snapshots,
occupied targets, stale revisions/observations, duplicate operations, missing or
incomplete feedback, unrelated execution, moved bystanders and failure blocking.
Simulator and hardware adapters must add their own measured integration tests.
