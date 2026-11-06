# camera-manipulation

Requires a prepared one-piece environment.json and native vision/motion libraries.

Install the environment using the [module guide](../../README.md). Run these
commands from the repository root. Set $bundle or $config to the documented
matching input, and $previous to a complete prior run directory.

~~~powershell
$ErrorActionPreference = 'Stop'
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$experiment = 'simulation/mujoco/training/camera-manipulation/runs/marker-visibility-832e62a9029a415f9e543b452f7bea77'
$config = Join-Path $experiment 'task/environment.json'
if (-not (Test-Path -LiteralPath $config)) { throw "Fixture missing. Generate it using the module README." }
& $py simulation/mujoco/training/camera-manipulation/run.py --config $config --camera-only --mode smoke --steps 32
~~~

This block creates a new run directory automatically. Existing generated
fixtures are local artifacts. If the referenced fixture is absent, follow the
module README to generate a reference scene and one-piece environment first.


Each invocation creates a fresh directory under training/camera-manipulation/runs/ unless
--output supplies another fresh destination. Read run.json for configuration and
lineage, report.json for completion and evaluation, and episode logs for failures.
A failed run may lack a final report. Retain partial checkpoints and logs.

Resume validates the recorded environment and checkpoint identity. Changes to
policy spaces require an explicit transfer or a new training run. Training with
the wrist model is pending integration. These commands use the existing
five-actuator workflow.

See the [training index](../README.md) for preserved checkpoints and limitations.

## Camera-only reward experiment

The canonical launcher accepts --camera-only. Use a newly generated H-file
marker scene and its environment.json.

~~~powershell
$ErrorActionPreference = 'Stop'
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$experiment = 'simulation/mujoco/training/camera-manipulation/runs/marker-visibility-832e62a9029a415f9e543b452f7bea77'
$config = Join-Path $experiment 'task/environment.json'
if (-not (Test-Path -LiteralPath $config)) { throw "Fixture missing. Generate it using the module README." }
$baseline = Join-Path $experiment ('baseline-' + [guid]::NewGuid().ToString('N'))
$smoke = Join-Path $experiment ('smoke-' + [guid]::NewGuid().ToString('N'))
& $py simulation/mujoco/training/camera-manipulation/run.py --config $config --camera-only --mode baseline --output $baseline
if ($LASTEXITCODE -ne 0) { throw 'Baseline failed. Inspect its failure.json.' }
& $py simulation/mujoco/training/camera-manipulation/run.py --config $config --camera-only --mode smoke --steps 32 --output $smoke
~~~

CameraOnlyEnv uses RGB for actor inputs, task reward and success candidates.
It requires visible source-piece evidence at reset and repeated destination
evidence after retreat. Static robot geometry and host command history provide
the nominal trajectory and phase. Synthetic empty-board images calibrate
foreground detection. Hardware deployment requires measured calibration.

The mode reports grasp and collision metrics as unavailable. Camera evidence
cannot establish physical grip, upright placement or release. Current camera-only
experiments use five actuator commands. Wrist policy migration remains pending.
See ADR S013 for the contract and limitations.

Artifacts include run.json, report.json or failure.json, policy.zip when training
completes, and camera-final.png plus homography-final.png after baseline evaluation.
A new reward mode requires a separate training lineage.

## Qualified RGB-only cycle on 2026-11-06

The previous retreat pose left the gripper over the destination. The environment
now returns to the configured observation pose before accepting camera success.
Three distinct native observations must show an empty source and a candidate of
the expected color at the target. The initial source candidate is required.

The following integration check blocks RewardEvaluator.read and executes the
entire nominal cycle. It passed in 109 steps on the generated H-file fixture.

~~~powershell
$env:ATOM_CAMERA_ONLY_CONFIG = $config
& $py -B -m pytest simulation/mujoco/tests/test_camera_only.py -q
~~~

The PPO experiment uses MultiInputPolicy with a 96x96 rectified RGB image,
source/target coordinates, prior action, commanded joint history, phase and
perception validity. Four bounded residual actions adjust nominal X/Y/Z and
finger opening. PPO updates its actor and value-network weights from RGB-only
episode rewards. The baseline already executes the nominal transfer, so this
experiment does not establish an advantage over deterministic planning.

The reward contains a time penalty, action penalty, visual-success reward and
perception/timeout failure penalty. Grip and collision metrics are unavailable.
The actor and reward do not read live piece poses or contacts. MuJoCo remains
the physics engine and the low-level position servo uses its simulated state.
This is an experimental one-piece simulation workflow. Wrist control, arbitrary
pieces, captures, physical grasp verification and hardware qualification remain
pending.

The current complete experiment directory is
runs/marker-visibility-832e62a9029a415f9e543b452f7bea77/.
Its camera-only-park-01 directory contains the verified baseline.
camera-only-ppo-2048-01 contains the new training lineage and checkpoint files.
Use the config in task/environment.json for this particular preserved run.

[Raw camera evidence](runs/marker-visibility-832e62a9029a415f9e543b452f7bea77/camera-only-park-01/camera-final.png)
and [rectified homography](runs/marker-visibility-832e62a9029a415f9e543b452f7bea77/camera-only-park-01/homography-final.png)
show the arm returned and the piece visible at the destination.

To continue this RGB-only lineage, keep --camera-only and pass the complete
previous run directory. The launcher verifies source/configuration identities
and policy SHA-256 before loading the optimizer and policy state.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$previous = 'simulation/mujoco/training/camera-manipulation/runs/marker-visibility-832e62a9029a415f9e543b452f7bea77/camera-only-ppo-2048-01'
$config = 'simulation/mujoco/training/camera-manipulation/runs/marker-visibility-832e62a9029a415f9e543b452f7bea77/task/environment.json'
& $py simulation/mujoco/training/camera-manipulation/run.py --camera-only --config $config --mode train --resume $previous --steps 2048
~~~

For an independent checkpoint evaluation, use --mode evaluate --checkpoint
(Join-Path $previous policy.zip) and retain --camera-only. Add --watch to
observe the physics viewer. The preserved camera and rectified images show the
perception viewpoint separately from the movable physics viewer.
