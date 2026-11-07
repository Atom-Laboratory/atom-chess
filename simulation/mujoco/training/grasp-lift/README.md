# grasp-lift

Requires the original five-actuator bundle and matching environment version.

Install the environment using the [module guide](../../README.md). Run these
commands from the repository root. Set $bundle or $config to the documented
matching input, and $previous to a complete prior run directory.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $py simulation/mujoco/training/grasp-lift/run.py --help
& $py simulation/mujoco/training/grasp-lift/run.py --bundle $bundle --stage grasp --steps 128
& $py simulation/mujoco/training/grasp-lift/run.py --bundle $bundle --stage grasp --resume $previous --steps 128
& $py simulation/mujoco/training/grasp-lift/evaluate.py --bundle $bundle --run $previous
~~~

Each invocation creates a fresh directory under training/grasp-lift/runs/ unless
--output supplies another fresh destination. Read run.json for configuration and
lineage, report.json for completion and evaluation, and episode logs for failures.
A failed run may lack a final report. Retain partial checkpoints and logs.

Resume validates the recorded environment and checkpoint identity. Changes to
policy spaces require an explicit transfer or a new training run. Training with
the wrist model is pending integration. These commands document the existing
five-actuator workflow. No training was launched during reorganization.

See the [training index](../README.md) for preserved checkpoints and limitations.
