# camera-manipulation

Requires a prepared one-piece environment.json and native vision/motion libraries.

Install the environment using the [module guide](../../README.md). Run these
commands from the repository root. Set $bundle or $config to the documented
matching input, and $previous to a complete prior run directory.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $py simulation/mujoco/training/camera-manipulation/run.py --help
& $py simulation/mujoco/training/camera-manipulation/run.py --config $config --mode smoke --steps 32
& $py simulation/mujoco/training/camera-manipulation/run.py --config $config --mode train --resume $previous --steps 128
& $py simulation/mujoco/training/camera-manipulation/run.py --config $config --mode evaluate --checkpoint (Join-Path $previous policy.zip)
~~~

Each invocation creates a fresh directory under training/camera-manipulation/runs/ unless
--output supplies another fresh destination. Read run.json for configuration and
lineage, report.json for completion and evaluation, and episode logs for failures.
A failed run may lack a final report. Retain partial checkpoints and logs.

Resume validates the recorded environment and checkpoint identity. Changes to
policy spaces require an explicit transfer or a new training run. Training with
the wrist model is pending integration. These commands document the existing
five-actuator workflow. No training was launched during reorganization.

See the [training index](../README.md) for preserved checkpoints and limitations.
