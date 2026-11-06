# MuJoCo example catalog

Run from the repository root in Windows PowerShell. Start with the
[module README](../README.md) for installation and the complete P038 setup.
Each example below uses a fresh output directory.

## Which bundle belongs to each example?

A bundle is a directory containing model.xml and manifest.json. Filenames are
labels. Joint names, actuators, pieces, geometry and model hashes define
compatibility.

| Example | Argument | Required input | Example prepared here |
|---|---|---|---|
| simulation_playground.py | --bundle | Full interactive 32-piece scene, five actuator prototype | runs/playground-fingertip-only-v1 |
| train_visual_grasp.py | --bundle | Legacy v3 32-piece scene with white_pawn_e2 and grasp_center | runs/playground-fingertip-only-v1 |
| replay_visual_grasp.py | --bundle and --run | Same model hash and environment as the saved v3 run | Original bundle and its matching legacy run |
| validate_native_perception.py | --bundle | Interactive board scene with named squares/pieces | $base |
| validate_board_reference.py | --bundle | Same board size as the supplied marker layout | $base |
| prepare_camera_task.py | --bundle and --reference-scene | Base metadata plus matching marker-scene XML | $base and $reference/reference-scene.xml |
| preview_native_policy.py | --scene | Marker-scene XML with the expected joint names | $reference/reference-scene.xml |
| train_camera_manipulation.py | --config | P038 environment.json pointing to a one-piece fixture | $task/environment.json |
| qualify_saved_perception.py | --source and --bundle | Saved captures/evaluator files and their generating bundle | Homography output and $base |
| compare_perception_reproductions.py | --p033, --p034, --audit | Preserved historical/current runs and matching initial audit | See P036 protocol |
| inspect_joints.py | --bundle | Five-actuator interactive prototype with its inspection frames | runs/interactive-chess-v6 |

The tutorial creates these related artifacts together.

~~~text
$work/
  base/                    $base, full robot + board + 32 pieces
  reference/
    reference-scene.xml    same base geometry + visual ArUco references
    initial-270-75.png     an RGB capture for native integration tests
  task/
    model.xml              P038 one-piece physical fixture
    manifest.json          exact model and asset identities
    environment.json       $config, task/camera/library/bundle selection
  smoke/
    run.json               recorded training environment signature
    policy.zip             compatible policy checkpoint
~~~

For P038, pass the task configuration. The program loads its bundle from the
configuration. For replay/resume, preserve the model/configuration/source hashes
recorded by the run. A 32-piece Playground bundle cannot replace a P038 one-piece
fixture. A checkpoint from legacy v3 has a different observation/action contract.

All current prototype bundles omit the physical 360-degree wrist rotation
reported by the user. P038 models J1, Z, J2 and two coupled finger slides.
Use these examples to study the existing prototype. Wrist-axis CAD mapping and
the corresponding new bundle/checkpoint version remain pending.

## Functional camera-guided manipulation

After completing the module README's preparation, keep these variables in the
same terminal.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$config = Join-Path $task 'environment.json'
~~~

| Example | Purpose | Command options | Expected result |
|---|---|---|---|
| prepare_camera_task.py | New one-piece fixture | --bundle --reference-scene --layout --output | model.xml, manifest.json, environment.json |
| train_camera_manipulation.py | Watch nominal motion | --config --output --mode baseline --episodes 1 --watch | Approach through retreat, physical result in report.json |
| train_camera_manipulation.py | Short training cycle | --config --output --mode smoke --steps 128 --device cpu | PPO updates, policy.zip, reload check and evaluation |
| train_camera_manipulation.py | Longer training | --config --output --mode train --steps 100000 | Fresh policy and periodic checkpoints |
| train_camera_manipulation.py | Continue saved run | --mode train --resume PREVIOUS_RUN --steps 128 | Verified optimizer/timestep continuation in new output |
| train_camera_manipulation.py | Evaluate saved actor | --mode evaluate --checkpoint POLICY_ZIP --episodes 2 --watch | Both nominal and residual results |

Exact commands are in the [module README](../README.md) and
[P038 guide](../../../docs/camera-rl/P038-camera-guided-manipulation.md).
See the [pipeline walkthrough](../../../docs/camera-rl/P038-pipeline-walkthrough.md)
for image sources, actor features, motion execution and PPO weight updates.

The current default task is a fixed e4-to-e5 pawn transfer. Success is verified
through a separate simulator evaluator. Native visual manipulation confirmation
remains unqualified. The smoke test establishes execution, rather than a learned
advantage or hardware readiness.

## Native camera-to-policy preview

Use the reference scene generated during setup. This example captures a static
configured observation pose and displays raw/rectified RGB.

~~~powershell
$out = Join-Path $work 'camera-preview'
& $py -B simulation/mujoco/examples/preview_native_policy.py --scene (Join-Path $reference 'reference-scene.xml') --layout docs/camera-rl/evidence-p035/high-camera-layout.json --library build/p038-core/bin/Release/acvision_runtime.dll --output $out --frames 30 --empty-fixture --preview
~~~

Expected files include camera.png, rectified.png, actor-input.png when reference
detection succeeds, empty-reference.png and report.json. This preview has a
fixed scene and creates no policy checkpoint.

## ArUco homography captures

~~~powershell
$out = Join-Path $work 'homography'
$exe = (Resolve-Path build/p038-core/bin/Release/perception_image.exe).Path
& $py -B simulation/mujoco/examples/validate_board_reference.py --bundle $base --assets docs/camera-rl/aruco-assets-v4 --layout docs/camera-rl/evidence-p035/high-camera-layout.json --executable $exe --output $out --elevations -75 --save-evaluator
~~~

The output contains input PNGs, native observation directories, rectified
overlays where accepted, independent evaluator-only points and report.json.
The detector gets RGB and layout. Only the evaluator gets projected truth.

## Paired checker/ArUco comparison

Use the output above so that evaluator-only files are available.

~~~powershell
$paired = Join-Path $work 'paired'
& $py -B simulation/mujoco/examples/qualify_saved_perception.py --source $out --bundle $base --layout docs/camera-rl/evidence-p035/high-camera-layout.json --executable $exe --output $paired
~~~

Read report.md, metrics.json, configuration.json and completion.json.
This example measures perception. It performs no training.

## Native integration tests from newly generated fixtures

~~~powershell
$env:P038_CONFIG = (Resolve-Path $config).Path
$env:ACVISION_RUNTIME_DLL = (Resolve-Path build/p038-core/bin/Release/acvision_runtime.dll).Path
$env:ACVISION_PERCEPTION_EXE = (Resolve-Path build/p038-core/bin/Release/perception_image.exe).Path
$env:ACVISION_TEST_IMAGE = (Resolve-Path (Join-Path $reference 'initial-270-75.png')).Path
$env:ACVISION_TEST_LAYOUT = (Resolve-Path docs/camera-rl/evidence-p035/high-camera-layout.json).Path

& $py -B -m pytest simulation/mujoco/tests/test_camera_manipulation.py simulation/mujoco/tests/test_native_runtime.py simulation/mujoco/tests/test_native_perception.py -q -p no:cacheprovider
~~~

Expected result is 31 passing tests with all prerequisites installed.
Unset the opt-in environment variables when running unrelated tests.

## Older experiments

- simulation_playground.py is the interactive multi-piece GUI. Start it using
  Start-MuJoCo.ps1 -Mode playground.
- train_visual_grasp.py and replay_visual_grasp.py use the preserved v3 pixel
  grasp/lift environment. Their checkpoints are separate from P038.
- inspect_joints.py inspects a specified bundle. Supply a new --output filename.
- validate_native_perception.py reproduces the earlier checker-only camera sweep.
- simulation/learning is a separate legacy URDF/SAC exercise. Read its README
  and use an independent virtual environment for its pinned dependencies.

For every future example, add a catalog entry with prerequisites, an exact
command, expected artifacts, test command and relevant limitations.
