# simulation_playground

Launch ATOM Chess Simulation Playground, or execute a headless task.

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
& $py simulation/mujoco/examples/simulation_playground/run.py --help
~~~

Supply the required inputs listed below. The directory entry point accepts
the same arguments as [the original script](../simulation_playground.py).

| Argument | Required | Default | Description |
|---|---|---|---|
| --bundle | True |  |  |
| --headless | False |  |  |
| --source | False | 'e2' |  |
| --target | False | 'e3' |  |
| --request | False |  | 'Versioned JSON from the Chess Core integration adapter' |
| --controller | False | 'baseline' |  |
| --output | False |  |  |
| --diagnostic-unchecked | False |  | 'Explicit experimental manipulation without swept preflight; never RL qualification' |
| --execute-trajectory | False |  | 'Execute an exported C++ P015 trajectory' |

## Results

Use a fresh path under this example for every new execution.

~~~powershell
$run = Join-Path simulation/mujoco/examples/simulation_playground/results ([guid]::NewGuid().ToString('N'))
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
