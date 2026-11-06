# prepare_camera_task

Create an exclusive one-piece camera-RL fixture from preserved ATOM scene assets.

## Prerequisites and input selection

Run from the repository root in Windows PowerShell. Install the environment
and native dependencies using the [module README](../../README.md).
Consult the [example catalog](../README.md) for bundle preparation and full
workflow commands. Match the bundle, configuration and checkpoint identities.
The six-actuator wrist profile currently supports the manual viewer. Automatic
planning and training migration is in progress.

## Run and inspect arguments

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $py simulation/mujoco/examples/prepare_camera_task/run.py --help
~~~

Supply the required inputs listed below. The directory entry point accepts
the documented arguments in [the implementation](run.py).

| Argument | Required | Default | Description |
|---|---|---|---|
| --bundle | True |  |  |
| --reference-scene | True |  |  |
| --layout | True |  |  |
| --output | True |  |  |
| --piece | False | 'white_pawn_e2' |  |
| --source | False | 'e4' |  |
| --target | False | 'd5' |  |

## Results

Use a fresh path under this example for every new execution.

~~~powershell
$run = Join-Path simulation/mujoco/examples/prepare_camera_task/runs ([guid]::NewGuid().ToString('N'))
~~~

For a directory-valued output argument, pass $run without precreating it.
For a file-valued output argument, create $run and choose a filename inside it.
Inspect --help and the workflow catalog before selecting the output type.
Examples without output arguments print their results or open a viewer.

[Existing results inventory](../existing-results.md) links preserved runs,
including model manifests, reports and checkpoints. A directory's existence
does not establish that its experiment succeeded.

## Verification

The --help command verifies that this entry point loads. Evaluate execution
using the report and failure fields produced by the selected workflow.
For simulation regressions run from the repository root.

~~~powershell
& $py -B -m pytest simulation/mujoco/tests -q
~~~

## Wrist and obstacle fixtures

The generator derives command dimensions from the bundle. A wrist bundle
receives a six-command observation pose with the wrist at half its bounded
revolution. --obstacle piece_name@square retains and places an additional
physical piece in the fixture. Repeat the option for multiple neighbors.
All obstacle names must exist in the input bundle.

For wrist physics and camera-only neighbor rewards, follow the full build,
reference generation and training commands in
[the training guide](../../training/camera-manipulation/README.md).
A generated fixture records obstacle identities in environment.json.
