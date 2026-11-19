# ATOM Chess Simulation Playground — initial implementation

Date: 2026-11-05. This is an initial playground, not acceptance of all section-20
requirements. It uses the existing Simulation and native MuJoCo viewer, without
another physics engine. No validated RL checkpoint exists.

## Start

From Windows PowerShell at repository root, with the existing venv and v6 bundle:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
```

The launcher builds `assets/bundles/playground-board-v1` on first use. This experimental
layout puts E2 and E3 within the v6 arm workspace. Choose piece/source/destination
and press Execute MOVE. The controller is the
experimental deterministic baseline. The RL option is explicitly unavailable.
The native viewer supports camera rotation/zoom. Results are saved as unique JSON
files next to the bundle; status and diagnostics appear in the panel. Each task
resets to the standard arrangement; custom setup/FEN is not yet supported.

The current GUI executes synchronously; animated physics updates are displayed
but interactive cancellation/pause during task execution remains pending. Use
the existing manual controls application for manual physics pause and joint jogs.
No checkpoint history exists. Task history records phases, commands, robot and
piece positions for implemented baseline execution. No reward is invented.

## Required E2 to E3 acceptance test

```powershell
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $atomPy simulation/mujoco/playground/run.py --bundle simulation/mujoco/assets/bundles/playground-board-v1 --headless --source E2 --target E3 --piece white_pawn_e2
& $atomPy -m pytest simulation/mujoco/tests/test_playground.py -v
```

**Experimental layout result: COMPLETED_SIMULATION_ORACLE**. MuJoCo confirms
bilateral finger contact, lift, release and final pawn position within 2 mm of
E3 on both horizontal axes. Independent visual verification remains pending.

**Original v6 layout result: FAILED**, numerical IK residual approximately 0.0891 m
at the E2 source approach. In v6 the planar distance from J1 to E2 is 0.45255 m.
The J1-to-elbow and elbow-to-grasp-center planar lengths sum to 0.36454 m,
an upper bound on horizontal reach from J1 for this model. The radial shortfall
alone is approximately 0.08801 m. The task is rejected before arm movement;
The experimental layout and its limits are recorded in [ADR S011](../../docs/adrs/S011-playground-board-layout.md).

## API and implementation

```python
from atom_mujoco.playground import Playground
simulator = Playground('simulation/mujoco/assets/bundles/playground-board-v1')
result = simulator.execute(operation='MOVE', piece_id='white_pawn_e2',
                           source='E2', target='E3', controller='baseline', seed=0)
```

Numerical damped-Jacobian IK plans on separate MjData, leaving live physics intact.
It checks all waypoint reachability before execution. The experimental pawn-only
baseline commands approach, close, lift, transport, place, open and retreat.
Success requires physical pawn position and release checks; reaching the tool
target alone is insufficient. Verification is explicitly **simulation_oracle**,
not independent computer vision. visual_confirmed remains false. The baseline
has passed E2–E3 in the experimental layout. Integration with the supervision
FSM, Chess Core and hardware remains pending.

## Remaining acceptance work

- Audit board placement and actual robot/link/TCP reach with CAD evidence.
- Validate complete physical moves and unaffected-piece checks, not only tool IK.
- Add nonblocking execution, pause/step/speed, task cancellation and sensor display.
- Add validated FEN/custom pieces/obstacles and logical/physical reconciliation.
- Integrate fault injection and evidence-gated recovery rather than guessed retries.
- Add batch runner, CSV summary, repeatable snapshot loading and policy comparison.
- Add checkpoint inference only after policy training/export/parity validation.

These requirements remain open. No trained-RL comparison, independent visual
confirmation or full playground completion is claimed.
