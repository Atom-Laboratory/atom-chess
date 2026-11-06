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
policy spaces require an explicit transfer or a new training run. The quick-start fixture uses the historical
five-actuator workflow. The wrist curriculum section documents the new model.

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
cannot establish physical grip, upright placement or release. Historical camera-only
experiments use five actuator commands. New wrist fixtures use six commands.
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

## Destination curriculum

Camera-only configurations may provide task_targets, a list of distinct
algebraic destinations. The source remains fixed by the one-piece fixture.
Training selects a target with the episode RNG. The actor task vector, nominal
planner and visual verifier all receive that same destination. Configuration
is preserved independently from the current episode selection.

The curriculum environment version is 3. Evaluate with --episodes equal to the
number of targets to visit every configured target once in list order. Reports
and episode logs include the selected target. Evaluation supports only targets
from the configured list.

A changed curriculum uses --warm-start with a complete prior run directory.
The launcher validates its checkpoint hash and policy spaces, copies the policy
weights into a new PPO instance, and starts a fresh optimizer and step counter.
Use --resume for exact continuation of an unchanged curriculum and provenance.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$root = 'simulation/mujoco/training/camera-manipulation/runs/destination-curriculum-1794000238965866200'
$config = Join-Path $root 'environment.json'
$previous = 'simulation/mujoco/training/camera-manipulation/runs/marker-visibility-832e62a9029a415f9e543b452f7bea77/camera-only-resume-5f972775eb1c4b7ea5bf94047675abd0'
if (-not (Test-Path -LiteralPath $config)) { throw 'Generate a matching one-piece fixture and curriculum configuration first.' }
& $py simulation/mujoco/training/camera-manipulation/run.py --camera-only --config $config --mode train --warm-start $previous --steps 2048 --episodes 8
~~~

The first qualified destinations from e4 are d5, e5, f5, d4, f4, d3, e3 and f3.
The preserved target-qualification-1794000159443367500/report.json records the
deterministic visual baseline for every destination. Each passed. Since the
nominal planner already succeeds, training must be compared against that baseline.
These results concern one white pawn, a fixed camera and the five-actuator model.

To test target consistency across actor inputs and visual verification, set
ATOM_CAMERA_ONLY_CONFIG to the original fixture environment.json and run
python -m pytest simulation/mujoco/tests/test_camera_only.py -q.
The integration test also blocks privileged task reward reads.

The completed destination-curriculum-1794000238965866200/ppo-2048 experiment
passed all eight per-target evaluations after loading the saved checkpoint.
The nominal baseline also passed eight of eight. Eighteen completed training
episodes received camera confirmation. The new policy started with the prior
run's verified final weights and used a fresh optimizer.

[Detailed results](runs/destination-curriculum-1794000238965866200/ppo-2048/README.md)
and [per-target report](runs/destination-curriculum-1794000238965866200/ppo-2048/report.json)
are stored beside the policy. An additional f5 replay records raw RGB,
rectified homography and visual feedback.

## Wrist and full-gripper collision curriculum

The wrist-enabled actor has five residual actions (X, Y, Z, opening and wrist
angle), and observes six commanded actuator positions. The two finger commands
remain coupled. Native IK accounts for the rotated offset between the wrist
axis and the grasp center. The wrist stays within its bounded revolution.
New wrist policies require fresh initialization because the old spaces differ.

Build the physical collision profile and a sparse-neighbor fixture from the
repository root after installing the Python environment and native libraries.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$work = Join-Path simulation/mujoco/training/camera-manipulation/runs ('wrist-full-' + [guid]::NewGuid().ToString('N'))
$base = Join-Path $work 'base'
$reference = Join-Path $work 'reference'
$task = Join-Path $work 'task'
$exe = (Resolve-Path build/p038-core/bin/Release/perception_image.exe).Path
& $py -B -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --parameters simulation/mujoco/playground/configs/playground-reachable-board.json --output $base --interactive --wrist --full-gripper-collision
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
& $py -B simulation/mujoco/examples/validate_board_reference/run.py --bundle $base --assets docs/camera-rl/aruco-assets-v4 --executable $exe --output $reference
if ($LASTEXITCODE -ne 0) { throw 'Reference generation failed' }
& $py -B simulation/mujoco/examples/prepare_camera_task/run.py --bundle $base --reference-scene (Join-Path $reference 'reference-scene.xml') --output $task --obstacle white_pawn_d2@c4
if ($LASTEXITCODE -ne 0) { throw 'Fixture preparation failed' }
$config = Join-Path $task 'environment.json'
& $py -B simulation/mujoco/training/camera-manipulation/run.py --camera-only --config $config --mode smoke --steps 128
~~~

The fixture starts the moving pawn on e4, targets d5 and places a physical pawn
on c4. Repeat --obstacle piece_name@square for additional neighbors. Target
curricula must exclude occupied obstacle squares. Generation validates distinct
identities and locations. All retained pieces are free rigid bodies.

The full profile uses 66 existing CAD-derived convex parts attached to the
rotating back and moving fingers, plus the fingertip contact pads. Bundle
manifests hash every included asset. Source mesh hashes are checked before
attaching the decomposition. Hardware calibration, complete linkage accuracy
and robot self-collision qualification remain pending.

CameraOnlyEnv compares the rectified images of each neighbor cell at reset and
after the arm returns to its observation pose. A changed pixel fraction above
0.03 rejects the transfer, even if the main piece reached its target. A graded
penalty reflects that fraction. Thresholds are experimental for fixed lighting.
This detects visual disturbance, including some displacements or toppling, but
does not prove every neighbor stayed physically upright or never moved.

The d4 adjacent-neighbor baseline was rejected with NEIGHBOR_VISUAL_CHANGE.
The c4 sparse-neighbor baseline passed with zero changed fraction.
Keep the d4 failure as a harder curriculum case. Do not equate successful
isolated grasping with a qualified crowded-board controller.

For integration checks, set ATOM_WRIST_CONFIG and ATOM_NEIGHBOR_CONFIG to matching
generated fixtures and run the following command.

~~~powershell
& $py -B -m pytest simulation/mujoco/tests/test_wrist_training.py -q
~~~

Recorded experiments are under
runs/wrist-c75050a5fba7486bae0b60e6c40ce766/.
ppo-wrist-1024 trains the isolated wrist model. full-gripper/ contains full
collision baselines, neighbor before/after images, the rejected d4 sweep and
the sparse-neighbor training. Each run records source identities and model
hashes. The isolated wrist run also preserves a Python source snapshot.


The wrist residual is rate limited to 0.4 rad/s by default, configurable through
wrist_residual_speed_rad_s. This prevents random exploration from continuously
interrupting the phase dwell condition. wrist_residual_rad sets the angular
residual range, initially 0.35 rad. The gripper inspection pose remains explicit
in initial_command. Episode reports include accumulated commanded wrist travel.

The completed isolated wrist run trained 1,024 steps and passed 3/3 final visual
evaluations. The first unsmoothed full-gripper experiment timed out during noisy
pregrasp exploration. The corrected sparse-neighbor run trained 1,024 steps,
passed 2/2 final evaluations with zero detected visual change in c4, and
preserved its source snapshot. An additional final-policy replay was executed
with privileged task-reward reads blocked. The d4 dense-neighbor case remains
a documented failure for subsequent curriculum work.

[Final sparse-neighbor run](runs/wrist-c75050a5fba7486bae0b60e6c40ce766/full-gripper/ppo-neighbor-smooth-1024/README.md)
contains the report, checkpoints, source snapshot and camera replay images.
