# Chess Core and motion integration audit

| Existing interface | Finding |
|---|---|
| `ac::chess::Board`, `Move`, MoveValidator | Chess Core owns legality and logical state. A validated move carries capture, en passant, castling and promotion metadata. |
| `ac::motion::TaskPlanner::planTasks` | Uses the pre-move Board, calibrated CoordinateMapper and GraveyardAllocator. Captured-piece removal precedes attacker movement. Allocation happens at planning time. |
| `PhysicalTask`, MotionPlanner, MotionExecution | Tasks carry piece type/color and optional endpoints in millimetres. Segment acknowledgements alone cannot confirm a physical transfer. |
| P005 supervision | Persistent task identity and evidence gates are available. The Playground has yet to use them. |
| S010/S011 Playground | Requires a piece ID, resets on each call and only attempts pawn manipulation. Waypoint IK provides endpoint reachability. Swept collision checks, self-collision and a simulated Graveyard are absent. The experimental E2–E3 regression uses simulator state for confirmation. |

The current Playground reset discards the result of prior transfers. Its piece
name contains the initial square, so names cannot serve as live occupancy.
The scene uses metres in its own frame. TaskPlanner coordinates use millimetres
in the robot base frame. The experimental TCP and board placement lack physical
calibration, and available gripper and collision geometry is approximate.

## ADR and implementation sequence

1. [P006](../adrs/P006-chess-motion-square-boundary.md) defines and tests the
   C++ adapter for one board transfer from the actual TaskPlanner.
2. [P007](../adrs/P007-confirmed-physical-board-state.md) now specifies and tests
   physical snapshots and operation lifecycle. Index all squares,
   piece identities and poses, held pieces and Graveyard slots. Preserve the
   last confirmed snapshot on failure and record uncertain live observations
   separately. Resolve square-only requests against that snapshot.
   See the [state adapter guide](physical-state-guide.md). This is an in-memory
   contract; [P008](../adrs/P008-live-playground-state-and-request-transport.md)
   adds live scene classification and Playground wiring.
3. P008 defines backend transport and routes Playground source/target selection through
   the same request interface. Separate explicit scene initialization from
   execution so that verified moves can form a sequence.
4. Define Graveyard geometry and transactional slot reservations. Map the
   existing ordered capture plan into typed endpoints. Reconcile each verified
   removal and keep the compound operation incomplete if its second step fails.
5. Define geometric planning and continuous collision validation. Document
   experimental TCP and all shape sources, allowed grasp/support contact pairs,
   held-piece swept geometry and self-collision coverage before enabling execution.
6. Connect supervision and physical feedback through grasp, lift, transport,
   placement and release. Confirm source, destination and unaffected pieces
   before committing a physical snapshot. Exercise faults and recovery in the
   Playground, including incomplete captures and lost feedback.

RL training is gated on verified generic transfers, captures, Graveyard use,
swept collision validation and physical-state reconciliation.

## Verify increment 1

Run from the checkout root in Linux or WSL with the existing C++ dependencies.

```bash
cmake -S . -B build/headless -DACCHESS_BUILD_VIEWER=OFF
cmake --build build/headless -j 4
ctest --test-dir build/headless --output-on-failure
```

The adapter regression feeds a real Chess Core Board and Move into TaskPlanner
and verifies the returned E2–E3 request. It also exercises whole-plan rejection
and malformed endpoints. This test stops at the request boundary. The Playground
will consume that boundary after the physical-state and transport increments.
