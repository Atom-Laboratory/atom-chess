# ATOM MuJoCo simulation — start here

Run commands in Windows PowerShell from the repository root. This README is the
current operational entry point. Historical v3–v6 notes are available in Git
history and the linked profile documents.

## Choose the example you want to understand

| Goal | Entry point | What it does |
|---|---|---|
| Explore the robot and chessboard | Start-MuJoCo.ps1 -Mode playground | Existing interactive board/manual-control Playground |
| Watch one controlled transfer | P038 launcher --mode baseline --watch | C++ nominal planner, supervised physics, one pawn e4 to e5 |
| Watch a saved residual policy | P038 launcher --mode evaluate --checkpoint ... --watch | Same nominal plan with PPO local corrections |
| Test the training loop | P038 launcher --mode smoke --steps 128 | New PPO, short optimization, save/reload and evaluation |
| Study image acquisition and weights | [Pipeline walkthrough](../../docs/camera-rl/P038-pipeline-walkthrough.md) | Source-by-source explanation |
| Run perception-only examples | [Examples README](examples/README.md) | Homography, reference and camera-to-policy checks |

The current prototype has J1, Z, J2 and two coupled finger slides. The physical
360-degree wrist rotation is a newly confirmed missing axis. Existing P038
checkpoints describe the five-actuator prototype and need an explicit migration
after that axis is modeled.

The current P038 pipeline is MuJoCo RGB -> native acvision -> validated policy
features -> PPO residual -> C++ acmotion IK and collision supervision -> physics.
Reward uses a separate simulator evaluator. Visual manipulation confirmation
remains experimental. The nominal baseline already succeeds on the fixed
one-piece fixture, so smoke success does not demonstrate an RL improvement.

## 1. Install Python dependencies

Reuse the existing .venv when available. For a fresh checkout with Python 3.12:

~~~powershell
py -3.12 -m venv simulation/mujoco/.venv
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $py -m pip install -r simulation/mujoco/requirements-windows-py312.lock
& $py -m pip install -e 'simulation/mujoco[test,rl]'
& $py -m pip check
~~~

The existing local validation used Python 3.12, MuJoCo 3.17.0, Gymnasium 1.4.0,
Stable-Baselines3 2.9.2 and PyTorch 2.14.1. CPU supports the examples. CUDA requires
a compatible PyTorch installation. Check with the following command.

~~~powershell
& $py -c "import torch; print(torch.__version__, torch.cuda.is_available())"
~~~

## 2. Open the existing Playground

~~~powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode playground
~~~

The launcher creates its default bundle if absent. Use the control panel for
manual arm movement and Open (O) / Close (C). The board UI selects moves and
invokes the existing Chess Core integration. Its autonomous transfer engine is
the existing Playground baseline. P038 is a separate one-piece RL example.

The demo mode prints numerical control results in the terminal.

~~~powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode demo
~~~

## 3. Build native modules for camera RL

Prerequisites are CMake, a C++ compiler and OpenCV 4.12 with ArUco support.
This machine uses Visual Studio 18 2026 and OpenCV at D:/opencv. Adjust the
generator and OpenCV_DIR to your installation.

~~~powershell
cmake -S . -B build/p038-core -G 'Visual Studio 18 2026' -A x64 -DOpenCV_DIR=D:/opencv/build/x64/vc16/lib -DBUILD_TESTING=OFF -DACCHESS_BUILD_VIEWER=OFF -DACVISION_NATIVE_RUNTIME=ON -DACMOTION_NATIVE_RUNTIME=ON
cmake --build build/p038-core --config Release --target motion_runtime acvision_runtime perception_image
~~~

Expected outputs in build/p038-core/bin/Release include motion_runtime.dll,
acvision_runtime.dll and perception_image.exe with their OpenCV dependencies.
A Stockfish-not-found warning does not prevent the controlled physical task.

## 4. Prepare P038 from versioned source assets

Use a new tutorial directory each time. This sequence regenerates the robot
bundle, reference-scene XML and one-piece fixture. It works without old runs.

~~~powershell
$work = Join-Path simulation/mujoco/runs ('tutorial-' + [guid]::NewGuid().ToString('N'))
$base = Join-Path $work 'base'
$reference = Join-Path $work 'reference'
$task = Join-Path $work 'task'
$exe = (Resolve-Path build/p038-core/bin/Release/perception_image.exe).Path

& $py -B -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --output $base --parameters simulation/mujoco/playground/configs/playground-reachable-board.json --interactive

& $py -B simulation/mujoco/examples/validate_board_reference/run.py --bundle $base --assets docs/camera-rl/aruco-assets-v4 --layout simulation/mujoco/configs/perception/h-file-layout.json --executable $exe --output $reference

& $py -B simulation/mujoco/examples/prepare_camera_task/run.py --bundle $base --reference-scene (Join-Path $reference 'reference-scene.xml') --layout simulation/mujoco/configs/perception/h-file-layout.json --output $task

$config = Join-Path $task 'environment.json'
~~~

The intermediate reference command produces diagnostic images and the XML used
by the task preparer. Its original arm pose can occlude pieces. The P038 task
uses its own explicit observation pose. Read task/environment.json to inspect
the exact camera, source, target, initial arm command and reward settings.

Generated bundles, reports and checkpoints remain under ignored runs/.
Every output directory must be new. Original assets and prior results remain
preserved.

## 5. Watch the deterministic pick-and-place

~~~powershell
$baseline = Join-Path $work 'baseline'
& $py -B simulation/mujoco/training/camera-manipulation/run.py --config $config --output $baseline --mode baseline --episodes 1 --watch
~~~

Expected behavior is approach, descend, close, lift, transport, place, open and
retreat. The terminal/report identifies physical success or an explicit failure.
--watch opens a MuJoCo viewer. The actor camera remains the configured fixed
camera, independently of the viewer's interactive camera.

## 6. Run a short training and inspect its result

~~~powershell
$smoke = Join-Path $work 'smoke'
& $py -B simulation/mujoco/training/camera-manipulation/run.py --config $config --output $smoke --mode smoke --steps 128 --episodes 1 --device cpu
Get-Content (Join-Path $smoke 'report.json')
~~~

Expected outputs are run.json, report.json and policy.zip. The report records
128 training steps, weight hashes and checkpoint_reload_verified.
episodes.jsonl appears when an episode finishes. These checks demonstrate
execution of the training cycle. Always inspect actual success and failure
fields.

## 7. Evaluate, train longer or resume

~~~powershell
$evaluation = Join-Path $work 'evaluation'
& $py -B simulation/mujoco/training/camera-manipulation/run.py --config $config --output $evaluation --mode evaluate --checkpoint (Join-Path $smoke 'policy.zip') --episodes 2 --device cpu --watch

$training = Join-Path $work 'training'
& $py -B simulation/mujoco/training/camera-manipulation/run.py --config $config --output $training --mode train --steps 100000 --episodes 3 --device cpu

$resume = Join-Path $work 'resumed'
& $py -B simulation/mujoco/training/camera-manipulation/run.py --config $config --output $resume --mode train --resume $smoke --steps 128 --episodes 1 --device cpu
~~~

Use --device cuda if available. Longer runs are user-selected examples.
Resume checks the recorded source/configuration/checkpoint identities.
Changing those requires a fresh run. Evaluation runs both the zero-residual
baseline and loaded residual actor.

## 8. Run automated tests

A general run exercises available tests and skips opt-in native integrations.

~~~powershell
& $py -B -m pytest simulation/mujoco/tests -q -p no:cacheprovider
~~~

For P038 and native image integration after completing the preparation above:

~~~powershell
$env:P038_CONFIG = (Resolve-Path $config).Path
$env:ACVISION_RUNTIME_DLL = (Resolve-Path build/p038-core/bin/Release/acvision_runtime.dll).Path
$env:ACVISION_PERCEPTION_EXE = $exe
$env:ACVISION_TEST_IMAGE = (Resolve-Path (Join-Path $reference 'initial-270-75.png')).Path
$env:ACVISION_TEST_LAYOUT = (Resolve-Path docs/camera-rl/evidence-p035/high-camera-layout.json).Path

& $py -B -m pytest simulation/mujoco/tests/test_camera_manipulation.py simulation/mujoco/tests/test_native_runtime.py simulation/mujoco/tests/test_native_perception.py -q -p no:cacheprovider
~~~

The native runtime tests also use a saved RGB fixture. See the
[examples README](examples/README.md) for the fixture variable and an independent
way to regenerate it. P036 archived-run verification is opt-in and requires
the recorded source/artifact versions.

## Where to read next

- [Example catalog and test commands](examples/README.md).
- [Read the running pipeline](../../docs/camera-rl/P038-pipeline-walkthrough.md).
- [P038 interfaces, action/reward semantics and limitations](../../docs/camera-rl/P038-camera-guided-manipulation.md).
- [Perception and camera-RL documentation index](../../docs/camera-rl/README.md).
- [Gripper v6 geometry history](docs/gripper-v6.md).
- [Earlier visual-grasp study material](../../docs/reinforcement-learning/README.md).

For future changes, update this README and the example catalog with prerequisites,
an exact command, expected artifacts, test commands and current limitations.

## Known full-suite limitation

The legacy multipiece capture test test_physical_capture_removes_before_attacker
currently fails with GRIP_LOST_DURING_TRANSPORTING on this prototype.
The supervised operation stops and reports the failure. P038 one-piece transfer
and native-integration tests pass. Full arm/wrist parity and reliable captured-piece
transport remain separate work.

## Test the one-turn gripper wrist

Build a fresh experimental bundle from the repository root in Windows PowerShell.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$bundle = Join-Path simulation/mujoco/runs ('wrist-' + [guid]::NewGuid().ToString('N'))
& $py -B -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --parameters simulation/mujoco/playground/configs/playground-reachable-board.json --output $bundle --interactive --wrist
if ($LASTEXITCODE -ne 0) { throw 'Wrist bundle build failed' }
& $py -B -m atom_mujoco.cli view --bundle $bundle
~~~

Raise Z before testing near the board. Use the **wrist_joint** slider or its
minus and plus buttons to rotate between 0 and 6.283 rad. The two end poses
look alike but correspond to opposite ends of the joint travel. Press Reset to
return to the simulated home. O and C still open and close the fingers
independently of wrist angle.

The Chess Playground and legacy capture entry points still require their five-actuator
bundles. The camera-manipulation training guide documents wrist-enabled fixtures. See
[ADR S010](../docs/adrs/S010-bounded-wrist-rotation.md) for the mesh-derived
pivot and the hardware switch calibration requirements.

~~~powershell
& $py -B -m pytest simulation/mujoco/tests/test_interactive.py -q
~~~

## Experiment ownership and migration

Demonstrations are indexed in [Examples](examples/README.md). Interactive work
belongs to [Playground](playground/README.md), whose reports use sessions/.
Learning and checkpoint evaluation belong to [Training](training/README.md),
with one complete run directory per experiment execution. New default training
outputs use training/<objective>/runs/. Existing artifact migration is pending
the [content inventory and proposal](docs/reorganization-audit-2026-11-06/README.md).

Historical commands below may still reference preserved runs/. Consult the
area guides above for current entry points and output ownership.

## Shared perception camera and wrist profile

The perception camera default lives in src/atom_mujoco/virtual_camera.py.
It views the board from the H-file side at azimuth 180 degrees and elevation
-75 degrees. The default aim point is the board center from the scene. The
interactive viewer orbit and legacy grasp policy camera are separate views.

Reference validation, native policy preview, one-piece fixture preparation and
the two-piece capture tools accept --camera-config. Pass a JSON file such as
{"azimuth": 270} to override only that setting. Use the same override and marker
layout throughout a test. Existing P038 environment.json files retain their
recorded camera. New fixtures record the resolved settings for reproducibility.

The Start-MuJoCo.ps1 view mode defaults to the wrist bundle. To use an existing
alternative bundle, pass -Bundle with its path. The wrist mounting geometry and
limits are defined in interactive_model.py and written into the generated model.
The automatic Playground and historical policies use the five-actuator profile.
New wrist-enabled camera policies use five actions and six commanded joints.

The centered two-piece capture passed with the shared camera. The one-piece
P038 baseline oriented successfully at reset but lost the board reference at
its first approach step. Treat the H-file camera as experimental for P038
until marker visibility is verified along the full trajectory.

## Full gripper collision profile

The build command accepts --wrist and --full-gripper-collision independently
with --interactive. The full-gripper option attaches the preserved 66 convex
parts to their actual moving bodies. The wrist model supports six-command
native IK and a five-action camera residual policy. See the
[training guide](training/camera-manipulation/README.md) for the staged
isolated-piece, full-collision and sparse-neighbor workflow.

The P038 launcher also supports a [live PPO dashboard and CSV export](training/camera-manipulation/README.md#live-dashboard-and-csv-exports).
For the opening pawn, see [FEN and RGB localization with intermediate checkpoint transfer](training/camera-manipulation/README.md#board-state-and-rgb-localization-for-the-full-board-pawn).
