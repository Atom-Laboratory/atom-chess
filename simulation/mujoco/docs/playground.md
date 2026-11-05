# ATOM Chess Simulation Playground — initial implementation

Date: 2026-11-05. This is an initial playground, not acceptance of all section-20
requirements. It uses the existing Simulation and native MuJoCo viewer, without
another physics engine. No validated RL checkpoint exists.

## Start

From Windows PowerShell at repository root, with the existing venv and v6 bundle:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
```

The launcher builds the v6 bundle on first use. Choose piece/source/destination
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
& $atomPy simulation/mujoco/examples/simulation_playground.py --bundle simulation/mujoco/runs/interactive-chess-v6 --headless --source E2 --target E3 --piece white_pawn_e2
& $atomPy -m pytest simulation/mujoco/tests/test_playground.py -v
```

**Result: FAILED**, numerical grasp-point IK best residual approximately 0.0891 m
at the E2 source approach. In v6 the planar distance from J1 to E2 is 0.45255 m.
The J1-to-elbow and elbow-to-grasp-center planar lengths sum to 0.36454 m,
an upper bound on horizontal reach from J1 for this model. The radial shortfall
alone is approximately 0.08801 m. The task is rejected before arm movement;
it is not counted as a successful pickup or board update. Do not silently relocate
the board, extend links or teleport a piece to pass this test.

## API and implementation

```python
from atom_mujoco.playground import Playground
simulator = Playground('simulation/mujoco/runs/interactive-chess-v6')
result = simulator.execute(operation='MOVE', piece_id='white_pawn_e2',
                           source='E2', target='E3', controller='baseline', seed=0)
```

Numerical damped-Jacobian IK plans on separate MjData, leaving live physics intact.
It checks all waypoint reachability before execution. The experimental pawn-only
baseline commands approach, close, lift, transport, place, open and retreat.
Success requires physical pawn position and release checks; reaching the tool
target alone is insufficient. Verification is explicitly **simulation_oracle**,
not independent computer vision. visual_confirmed remains false. The baseline
has not passed an end-to-end board move and is not integrated with the supervision
FSM or Chess Core. No physical hardware interface exists here.

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
