# Playground integration developer guide

## Current transport and execution

The C++ `ac::integration::serializeBoardMove(plan)` serializes the actual
TaskPlanner output into this versioned request (no piece identity):

```json
{"schema":1,"operation":"MOVE","source":"e2","target":"e3"}
```

Chess Core owns legal move validation. The integration caller supplies the complete
already validated plan and must not advance the authoritative logical Board on
request submission. The schema-1 serializer rejects compound plans; schema 2
supports ordered transfers with an explicit calibrated-XY-to-slot resolver.
Python does not implement chess legality. The Playground's square selectors test
the same physical request consumer; they are not a second chess game.

From the repository root in Windows PowerShell:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
# Or consume a request exported by the integration caller:
& ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/simulation_playground.py --bundle simulation/mujoco/runs/playground-board-v1 --headless --request path/to/request.json --output simulation/mujoco/runs/new-result.json
```

Click the source tile and then the target tile, or select the role explicitly.
Blue marks the source and gold marks the target in the panel and 3D viewer.
Both roles accept board squares and configured Graveyard slots. The grid shows
confirmed occupancy and refreshes after execution or reset.
Each successful transfer updates the confirmed physical revision. A second request
uses the resulting scene without resetting. For the experimental board fixture,
the diagnostic regression exercises E2 to E3 and back to E2 with all 32 dynamic pieces.
This is limited manipulation evidence, not proof that every square is reachable.

## Feedback and failure

Initialization settles the scene once. `SceneFeedback` reads actual body poses,
velocities, orientation and pad contacts. It requires unambiguous square occupancy
and settled upright supported pieces. `MotionController` applies model bias-force
feedforward for arm gravity and waits for joint settling with a bounded timeout.
The geometric grasp hypothesis uses the simulated stem geometry; it does not
reconstruct the real servo linkage or establish CAD accuracy.

P005 gates verify the manipulation phases. P007 checks the final whole-board
candidate before the release gate can complete, then commits the revision.
Failures preserve the last confirmed state and require reconciliation. Current
process-local state is not a durable hardware transaction. A failed simulation
does not roll back physics, and stopping physics calls is not a hardware stop.

Result JSON identifies the simulation oracle, physical revision, failure detail
and phase history. RL remains unavailable. The default now requires nominal swept
preflight; see [P010](../adrs/P010-conservative-swept-preflight.md). Runtime contact
monitoring is also enabled. The checker reports structural exclusions, phase,
geometry names, joint configuration and distance. Unresolved checks fail closed.

**Known blocking geometry:** the current E2 descent intersects the conservative
finger hull with the D1 queen head (about 2.8 mm in the tested fixture). The normal
Playground therefore refuses this trajectory before physics advances. This may
reflect convex-hull overapproximation; it is not proof of a real CAD collision.
Do not disable this check to label the deterministic pipeline qualified for RL.

For reproduction of the earlier isolated manipulation evidence only, pass
`-DiagnosticUnchecked` with the PowerShell launcher in playground mode, or pass
`--diagnostic-unchecked` to the Python example. Results carry
`collision_checked=false` and `training_eligible=false`. The physical capture/return tests explicitly use
diagnostic mode; collision tests independently verify rejection without motion.

Use **Inspect trajectory / confirmed occupancy** to inspect all planned phases
and confirmed state. **Execute Chess Core request file** consumes exported JSON.
The checker proves nominal geometric interval separation under its model and
rigid-grasp assumptions, not dynamic or hardware safety. Controller tracking,
collision shape repair and full workspace qualification remain unresolved.

## Captures and Graveyard

The launcher creates `runs/playground-graveyard-grid-v2` using the experimental
layout in `examples/playground-graveyard-grid.json`. It has 16 slots per color.
Black slots are behind rank 8 and white slots are behind rank 1.
Old bundles are preserved and still show their configured slots.
Add measured or explicitly experimental slots in a new parameter file and build
a fresh bundle when more capacity is required. Never recycle occupied slots.

The schema-2 consumer accepts a complete ordered task list from Chess Core:

```json
{"schema":2,"operation":"PLAN","transfers":[
  {"source":"e3","target":"graveyard:slot_0"},
  {"source":"e2","target":"e3"}
]}
```

This example requires an explicitly initialized position with a captured object
on E3. The whole plan is checked against projected occupancy before dispatch.
Successful removal commits first. If the attacker transfer fails, the captured
object remains confirmed in the Graveyard and the composite result is FAILED with
`completed_transfers=1`. Do not roll back the physical snapshot or mark the logical
move completed. The existing C++ allocator still requires application-level
reservation rollback/reconciliation; the serializer does not mutate it.

`test_task_plan.py` includes a diagnostic two-transfer physics regression with 32 objects:
a black pawn is initialized on E3, physically removed to slot_0, and the E2 pawn
then physically moved to E3. This does not establish collision safety, CAD fidelity
or reachability of every Graveyard slot. No pose edits occur during that execution.

## Verify

```powershell
& ./simulation/mujoco/.venv/Scripts/python.exe -m pytest simulation/mujoco/tests/test_playground.py simulation/mujoco/tests/test_physical_state.py -v
```

The C++ adapter regression separately checks the exact JSON produced from the
real TaskPlanner. Run the CMake/CTest instructions in `integration-revision.md`.

P015 adds experimental C++ MotionPlanner/IK playback. See docs/hybrid-control/p015-execution-guide.md. Legacy square-based Python planning remains active separately.

## Crowded-square grasp aperture (P024)

Select source and destination, then click Confirm MOVE. Selection alone does not
execute. Restart the Playground after a Python update; the existing fingertip
bundle need not be rebuilt for this planner change:

    & ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground

The baseline first narrows its jaws above the source, descends, grips at the
simulated stem diameter, lifts and transports. It releases partially, retreats,
and fully opens above the destination. Aperture values are recorded as
pregrasp_opening_m and grasp_opening_m. They are per-finger joint references,
not the total gap. The swept report includes preshape and fully_open intervals.

A COLLISION_PREFLIGHT_FAILED with a positive distance means the configured
1 mm clearance was violated; it need not imply overlapping geometry. Check
collision_report.phase and failure.geoms. Do not disable checks to force a move.
E2–E4 now completes in the experimental scene, including contact and release
verification. This does not qualify other layouts, CAD accuracy or hardware.
