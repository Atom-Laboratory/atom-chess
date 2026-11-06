# validate_board_reference

Render explicit experimental ArUco supports; native vision receives images/layout only.

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
& $py simulation/mujoco/examples/validate_board_reference/run.py --help
~~~

Supply the required inputs listed below. The directory entry point accepts
the same arguments as [the original script](../validate_board_reference.py).

| Argument | Required | Default | Description |
|---|---|---|---|
| --bundle | True |  |  |
| --assets | True |  |  |
| --layout | False |  | 'Alternative measured or experimental marker layout' |
| --executable | True |  |  |
| --output | True |  |  |
| --save-evaluator | False |  | 'Save independent projected board points after native execution' |
| --evaluate-foreground | False |  |  |
| --elevations | False | (-35, -45, -55) |  |
| --azimuths | False | (265, 270, 275) |  |

## Results

Use a fresh path under this example for every new execution.

~~~powershell
$run = Join-Path simulation/mujoco/examples/validate_board_reference/results ([guid]::NewGuid().ToString('N'))
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
