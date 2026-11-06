# train_visual_grasp

Train and evaluate an experimental pixel-only PPO grasp policy.

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
& $py simulation/mujoco/examples/train_visual_grasp/run.py --help
~~~

Supply the required inputs listed below. The directory entry point accepts
the same arguments as [the original script](../train_visual_grasp.py).

| Argument | Required | Default | Description |
|---|---|---|---|
| --bundle | True |  |  |
| --output | True |  |  |
| --steps | False | 100000 |  |
| --seed | False | 7 |  |
| --eval-episodes | False | 10 |  |
| --device | False | 'auto' |  |
| --horizon | False | 100 |  |
| --stage | False | 'lift' |  |
| --watch | False |  |  |
| --speed | False | 2.0 |  |
| --warm-start | False |  | 'Import weights with a fresh optimizer' |
| --resume | False |  | 'Previous run directory; new output is required' |
| --warm-start-features | False |  | 'Transfer the visual encoder and initialize fresh policy heads' |
| --workers | False | 1 |  |
| --arena | False |  | 'Mirror all workers in one 3D scene' |

## Results

Use a fresh path under this example for every new execution.

~~~powershell
$run = Join-Path simulation/mujoco/examples/train_visual_grasp/results ([guid]::NewGuid().ToString('N'))
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
