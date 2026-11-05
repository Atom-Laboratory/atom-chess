# Playground integration developer guide

## Current transport and execution

The C++ `ac::integration::serializeBoardMove(plan)` serializes the actual
TaskPlanner output into this versioned request (no piece identity):

```json
{"schema":1,"operation":"MOVE","source":"e2","target":"e3"}
```

Chess Core owns legal move validation. The integration caller supplies the complete
already validated plan and must not advance the authoritative logical Board on
request submission. Unsupported compound plans are rejected by the serializer.
Python does not implement chess legality. The Playground's square selectors test
the same physical request consumer; they are not a second chess game.

From the repository root in Windows PowerShell:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
# Or consume a request exported by the integration caller:
& ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/simulation_playground.py --bundle simulation/mujoco/runs/playground-board-v1 --headless --request path/to/request.json --output simulation/mujoco/runs/new-result.json
```

Choose Source and Target, then Execute MOVE. No piece selection is required.
Each successful transfer updates the confirmed physical revision. A second request
uses the resulting scene without resetting. For the experimental board fixture,
the regression exercises E2 to E3 and back to E2 with all 32 dynamic pieces.
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
and phase history. RL remains unavailable. At this increment, complete swept
collision checking, Graveyard execution and recovery remain subsequent work.

## Verify

```powershell
& ./simulation/mujoco/.venv/Scripts/python.exe -m pytest simulation/mujoco/tests/test_playground.py simulation/mujoco/tests/test_physical_state.py -v
```

The C++ adapter regression separately checks the exact JSON produced from the
real TaskPlanner. Run the CMake/CTest instructions in `integration-revision.md`.
