# Native hybrid approach qualification (M2)

This experiment executes a collision-checked approach from park to above a
camera-localized piece, then retreats. It uses the existing native C++ planner
and IK. The opt-in M4 local diagnostic additionally attempts guarded descent,
closure and lift. It does **not** train or invoke an RL policy, qualify an entire
contact manipulation workspace, or qualify carried-object transport.

## Prerequisites and Windows commands

Run PowerShell from the repository root, not your Windows home directory.
Install the MuJoCo environment using the module README. A prepared wrist-aware
environment JSON must reference an intact bundle, the native vision/motion DLLs
and an oriented board-reference layout. The example below uses the preserved
32-piece starting-position fixture; paths inside that JSON must exist locally.

```powershell
# Run from the repository root.
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$config = 'simulation/mujoco/training/camera-manipulation/runs/pawn-e2-e4-vision-fen-v1/environment.json'
& $py -u -B simulation/mujoco/examples/qualify_hybrid_approach/run.py --config $config
```

Watch opens by default before planning. The robot remains stationary during
planning and live-scene preflight. After validation it approaches and returns;
the final window remains open until closed. The window overlay distinguishes
planning, verification, approach, retreat and rejection. This is a qualification
viewer, not a training dashboard. `--headless` explicitly disables Watch;
`--plan-only` skips execution. `--seed 7` is the reproducible default.
`--max-candidates 48` bounds the candidate family. `--speed-fraction .25`
caps commanded joint speed at 25% of manifest velocity using quintic rest-to-rest
timing; it does not change joint limits, collider geometry or collision clearance.

## M4 local supervisor diagnostic

```powershell
& $py -u -B simulation/mujoco/examples/qualify_hybrid_approach/run.py `
  --config $config --local-diagnostic --grasp-part stem --max-local-decisions 1000
```

This leaves the arm at the verified approach instead of retreating, performs
one checked local descent probe and screens the full descent before attempting
rate-limited local proposals. It stops if any screen/action/feedback gate fails.
Watch shows `M4 / LOCAL SUPERVISOR - NO RL` and actual qualification ownership.
It remains open on the final diagnostic status. `--plan-only` cannot be combined
with `--local-diagnostic`. `--max-local-decisions` is a software decision budget,
not PPO training steps.

`--grasp-part head` selects the existing sphere/cylinder head center and radius
instead of the stem. It retains the existing experimental 3 mm side gap and
0.5 mm closing interference. It does not change CAD, scale, collider dimensions,
collision masks or the 1 mm swept-check clearance. The current diagnostic is
intended for the pawn fixture; unsupported head geometry fails explicitly.

`--closing-load-factor 1.65` optionally derives an experimental closing preload
from model mass, gravity, friction and finger position gain. The default retains
the old 0.5 mm interference. Force/travel limits and complete sweeps still apply.
`--lift-speed-fraction .25` limits the deterministic lift proposal's XYZ speed;
it does not change a policy action after submission. Failed load/speed trials
remain recorded and do not qualify training or manipulation.

To compare the same physics with only the selected piece, reuse the existing
preparation tool, with a **fresh** fixture path:

```powershell
$fixture = Join-Path 'simulation/mujoco/examples/qualify_hybrid_approach/runs' ('isolated-fixture-' + [guid]::NewGuid().ToString('N'))
& $py -B simulation/mujoco/training/autonomous-manipulation/prepare.py `
  --config $config --output $fixture --isolated --parked
$isolatedConfig = Join-Path $fixture 'environment.json'
& $py -u -B simulation/mujoco/examples/qualify_hybrid_approach/run.py `
  --config $isolatedConfig --local-diagnostic --grasp-part head
```

Isolation removes neighbors and updates expected FEN through the existing
preparation interface. It retains source gravity, robot and full-gripper hulls.
Success on an isolated piece would not qualify a full-board grasp or physical
hardware. Source/target XY still comes from RGB localization; grasp-height
candidates use explicitly experimental static collision-model geometry.

## Outputs and evidence

Each invocation creates a fresh directory in this example's `runs/` directory.
An explicit `--output` must also be a new directory. Existing results are preserved.

- `provenance.json`: configuration, native-library and Python-source hashes,
  seed, MuJoCo version and timing setting.
- `plan.json`: complete candidate rejections, native IK choices, swept-path
  checks, derived geometry, observed RGB offsets, start/model identity, signed
  accepted trajectory and conservative entry-neighborhood certificate.
- `report.json`: measured joint/TCP traces, approach/retreat completion,
  runtime failures, tracking errors and privileged diagnostic piece displacement.
- `camera-initial.png`, `camera-approach.png` (only after verified arrival),
  `camera-final.png`: actual simulation RGB captures.
- `state-final.json`: privileged final qpos/qvel/control snapshot for diagnostic
  reproduction, never an actor input.
- With `--local-diagnostic`, `local-report.json` and `local-decisions.jsonl`:
  full local screens, actual commands/feedback, rejection pairs and elapsed
  execution/settling intervals. Completed stages also save `camera-local-*.png`.
- `failure.json`: traceback and explicit failed status if the experiment raises
  an exception; a partial run is not silently presented as successful.

`COMPLETED_SIMULATED_APPROACH` requires actual approach and requested retreat,
not just a successful IK solve. `REJECTED` means no command was issued; `FAILED`
may require reconciliation after partial movement. `PLANNED_ONLY` is not execution.
All outputs explicitly keep `training_eligible=false` and
`local_manipulation_workspace_qualified=false` in this M2 increment.

## Pipeline and boundaries

1. Native ac:vision localizes occupied squares from RGB relative to calibration
   images and the ArUco board reference. Static bundle geometry supplies the
   experimental board-to-robot mapping and collision shapes.
2. The existing native MotionPlanner generates its canonical eight Cartesian
   waypoints. This adapter uses their high-clearance positions for approach
   candidates, with in-limit wrist angles, elbow branches and model-derived heights.
3. Native IK returns joint targets. Python appends the bounded wrist command
   after deriving its effect on the TCP geometry. Complete joint paths and
   retreat are validated using SweptChecker, independently of physics contact masks.
4. Execution checks plan integrity, unchanged model/start, fresh RGB localization,
   board reference and the complete path against the actual simulation scene.
5. MotionController issues interpolated position targets. Physics feedback checks
   contact, toppling, displacement, dynamic joint excursion and settling.

Live body poses are permitted only for independent simulation safety and result
measurement. Camera localization and static robot geometry generate task endpoints.
No learned actor receives simulator state here because there is no actor yet.

The entry certificate is a **small collision-free joint box**, not an entire
grasp/lift workspace. Soft MuJoCo constraints can cause tiny measured joint
excursions. Execution reports a numerical tolerance equal to one physics-step
travel at each manifest joint velocity; this is not measured hardware accuracy.
The model, TCP, masses and contact parameters remain experimental.

## Tests

```powershell
& $py -B -m pytest simulation/mujoco/tests/test_hybrid_approach.py simulation/mujoco/tests/test_approach_sweep.py simulation/mujoco/tests/test_board_piece_localization.py -q
```

These test transformed collider bounds, quintic speed bounds, plan tampering,
changed model/scene/commands, invalid timing and RGB-only scene construction.
The runnable experiment separately tests actual native-library integration and
dynamic execution; unit tests alone cannot establish manipulation success.

See [ADR S029](../../../docs/adrs/S029-native-approach-qualification.md),
the [M1 audit](../../../../docs/camera-rl/hybrid-m1-audit.md) and the
[hybrid M2 result](../../../../docs/camera-rl/hybrid-m2-qualification.md).
See also the [M4 diagnostic report](../../../../docs/camera-rl/hybrid-m4-supervision.md)
and [ADR S031](../../../docs/adrs/S031-local-proposal-supervision.md).
