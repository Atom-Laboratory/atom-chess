# camera-manipulation

To study the full pipeline and rebuild it independently, start with the
[P038 camera PPO reconstruction guide](../../../docs/learning/camera-ppo/README.md).

## Screen distinct pickup approaches

The offline sweep uses the existing RGB-localized full-board E2/E1 wrist
fixture. Prepare that fixture using the board-state workflow below. The tool
requires the native AC:Vision and AC:Motion libraries, the RL Python extra,
and an OpenGL-capable MuJoCo installation. It runs endpoint screening first
and executes a pickup only after the conservative sweep passes. It records
physical and visual evidence separately and does not start PPO.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$root = 'simulation/mujoco/training/camera-manipulation'
$config = "$root/runs/pawn-e2-e4-vision-fen-v1/environment.json"
$output = "$root/runs/approach-$([guid]::NewGuid().ToString('N'))"
& $py -u -B "$root/approach_sweep.py" --config $config --output $output --seed 100007 --max-screen 2600 --max-sweep 6 --max-execute 4
& $py -B -m pytest simulation/mujoco/tests/test_approach_sweep.py -q
~~~

Inspect protocol.json and report.json for configuration, sample budget,
candidate waypoints, collision pair and measured clearance. RGB images are
saved for executed paths. The initial search uses fixed pickup Z and a
finite parameter grid. Its endpoint distance is sampled against the king.
Sweep acceptance covers a nominal joint-linear path with an approximate
held-pawn model. Execution evidence applies to the simulated fixture.
See the [research protocol](../../../../docs/camera-rl/approach-strategy-study.md).

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

## Touch penalties and the 90% qualification protocol

The policy observation remains RGB plus host command history. Setting
non_target_contact_penalty to a positive value enables simulation contact
supervision. The run reports rgb_plus_non_target_contacts as its reward source.
Each environment step with robot-to-non-target or carried-piece-to-non-target
contact receives a penalty, and execution continues. A piece tilting more than
60 degrees stops physics stepping at the detected substep, terminates the
episode and receives a larger toppling penalty. All pieces, including the
selected piece, are monitored for toppling. These are training-only privileged
signals and do not establish hardware sensing.

The qualification fixture uses the complete gripper colliders, a d4 neighbor,
and an e4-to-d5 transfer. It selects one wrist residual while elevated before
grasping and another while elevated before placement. The nominal source and
transport orientations are configured separately to clear different obstacle
directions. Setup-only random placement offsets are sampled within +/-1 mm.
The actor never receives the sampled physical offsets.

qualify.py evaluates a saved run against at least thirty fixed seeds. It checks source
and checkpoint identities, correct target appearance, stable neighbor images
and absence of toppling. Contacts are counted separately and do not automatically
reject an otherwise completed transfer. The 90% threshold applies to the
declared simulation test distribution. The historical sparse run stopped
after nine episodes with six approvals, so that run did not qualify.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$root = 'simulation/mujoco/training/camera-manipulation/runs'
$config = 'PATH_TO_THE_ENVIRONMENT_JSON_USED_TO_TRAIN'
$run = 'PATH_TO_THE_COMPLETED_RUN_DIRECTORY'
$output = Join-Path $root ('qualification-' + [guid]::NewGuid().ToString('N'))
& $py -B simulation/mujoco/training/camera-manipulation/qualify.py --config $config --run $run --output $output --episodes 30 --start-seed 910000 --minimum-rate .9
~~~

Use a completed run that matches the current source and model provenance.
For the historical sparse scenario, contact-environment.json records
visual_qualification=true, placement_jitter_m=0.001,
non_target_contact_penalty=20, the full-gripper fixture and phase-specific
wrist orientations. Preserve that configuration with its historical run.
Train a matching run on the current revision before qualifying this
scenario with the current launcher.

Outputs include protocol.json with the exact seed list, report.json with all
decisions, and before/after RGB and board images for each episode. A passed
field becomes true only when all requested episodes have completed and the
acceptance rate meets the target. Interrupted evaluations retain partial results.

Run tests with the MuJoCo Python environment.

~~~powershell
& $py -B -m pytest simulation/mujoco/tests/test_contact_supervision.py simulation/mujoco/tests/test_wrist_training.py -q
~~~

See ADR S016 for the appearance criteria and ADR S017 for the explicit split
between visual actor inputs and training-only contact/toppling supervision.

## Change the selected piece in a crowded fixture

Pass --piece with the model identity and --source with its starting square when
running examples/prepare_camera_task/run.py. For the center exercise use
--piece white_pawn_d2 --source d4 --target e5. The identity refers to the
original model piece and remains white_pawn_d2 after it is placed on d4.
Each repeated --obstacle name@square adds a separate dynamic neighbor. Keep
the source, target, neighbor squares and piece identities distinct.

Generate a new fixture when changing the selected piece or its starting square.
Editing only source in an existing environment.json changes the requested
square but does not move the physical piece in model.xml. For a compatible
curriculum, use --warm-start and keep the original checkpoint run intact.

Capture fixtures accept the same repeated --obstacle option on
examples/prepare_capture_task/prepare_capture_task.py. The RGB executor checks
neighbor images after each transfer. It first removes the captured pawn to
the Graveyard and then moves the attacker. Its swept preflight may reject
crowded configurations. It is a deterministic validation path.

## Standard opening exercises

Use [the fixture generator](../../examples/prepare_camera_task/README.md)
with --starting-position. The opening curriculum keeps all 32 pieces in
the scene and uses separate tasks for pawn e2 to e4 and knight g1 to f3.
Run each baseline separately before transferring policy weights. A legal
chess move can still fail the physical or visual checks.

## Board-state and RGB localization for the full-board pawn

Enable `localize_source_rgb` with a `board_fen` exported by Chess Core.
The simulation fixture and task endpoints must agree with the FEN. For the
opening pawn exercise, use the pre-move FEN and E2-to-E4 transfer returned
by `atom_mujoco.chess_commands.plan_move([], 'e2e4')`. This is an offline
snapshot of the logical game. The launcher does not subscribe to a live game.
To prepare a new configuration, start from the full-board pawn configuration
emitted by the fixture generator. Use a fresh directory under the training runs
folder. The Chess Core bridge described by the interactive Playground
must be available to export the pre-move FEN.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$base = 'FILL_IN_THE_GENERATED_PAWN_JSON_PATH'
$runs = 'simulation/mujoco/training/camera-manipulation/runs'
$prepared = Join-Path $runs ("pawn-e2-e4-rgb-" + [guid]::NewGuid().ToString('N'))
$fen = & $py -c "from atom_mujoco.chess_commands import plan_move; print(plan_move([], 'e2e4')['fen'])"
if ($LASTEXITCODE -ne 0) { throw 'Chess Core FEN export failed' }
$cfg = Get-Content $base -Raw | ConvertFrom-Json
$cfg | Add-Member -NotePropertyName board_fen -NotePropertyValue $fen
$cfg | Add-Member -NotePropertyName localize_source_rgb -NotePropertyValue $true
$cfg | Add-Member -NotePropertyName neighbor_displacement_penalty_per_mm -NotePropertyValue 1.0
$cfg | Add-Member -Force -NotePropertyName non_target_contact_penalty -NotePropertyValue 20.0
$cfg | Add-Member -Force -NotePropertyName visual_qualification -NotePropertyValue $true
New-Item -ItemType Directory $prepared | Out-Null
$config = Join-Path $prepared 'environment.json'
[IO.File]::WriteAllText((Join-Path (Get-Location) $config), ($cfg | ConvertTo-Json -Depth 12))
~~~

ACVision rectifies the RGB frame using the ArUco reference layout. The
localizer compares each logically occupied cell against a centered RGB
calibration and estimates its XY offset in the board plane. The source
estimate moves the AC:Motion pickup waypoint. Unknown offsets are omitted.
A missing source estimate aborts reset. The actor receives RGB, task squares,
commanded joints, its previous action, phase and the perception validity
flag. Its observation space is compatible with the previous opening policy.
The simulated robot still uses static geometry for the board-to-base
transform, TCP, gripper opening and joint limits. The real installation
requires equivalent calibration and its own empty and centered RGB
references. This fixture does not qualify a movable board or a real camera.

With `neighbor_displacement_penalty_per_mm` set to 1.0, a new maximum
displacement of a bystander costs one reward unit per millimeter beyond the
0.25 mm dead band. Returning toward the original point does not refund the
penalty. MuJoCo measures this displacement, contact and toppling for reward
and termination only. The camera still verifies final placement and neighbor
appearance. Individual grasp and lift bonuses require a separate validated
RGB verification step.

For an interrupted run, pass `--warm-start-checkpoint` with the intermediate
ZIP in its original run directory. Optionally pin it with
`--checkpoint-sha256`. The new run records the archive digest, saved
source steps, environment signature and weight digest in `run.json`.
Its `report.json` records the initial and final weight digests. For the
camera/FEN test, set `ATOM_CAMERA_FEN_CONFIG` to the generated environment
configuration, then run the following from the repository root.

~~~powershell
& .\simulation\mujoco\.venv\Scripts\python.exe -B -m pytest simulation/mujoco/tests/test_board_piece_localization.py simulation/mujoco/tests/test_contact_supervision.py simulation/mujoco/tests/test_camera_only.py -q
~~~

## Live dashboard and CSV exports

Add --dashboard to train or smoke mode to open the live Tk dashboard. On Windows,
use the repository's MuJoCo Python environment with Tk available. Add --watch
to open the MuJoCo viewer at the same time. The dashboard opens during baseline evaluation and shows the current stage.
It runs in a separate process from MuJoCo. Graph activations and losses appear
once PPO begins. After training ends, the window stays open for inspection.

The terminal and the dashboard header show the current stage and its
progress. For example, `Training PPO | 200/2048 steps (9.8%)` counts the
steps collected in the current execution, including when resuming a policy
with an existing lifetime counter. Baseline and saved-policy evaluations
show completed episodes and the current simulation step. If PPO must round
a step request up to a full rollout, the progress denominator is the rounded
total and the initial training message shows the original request.

- **PPO losses** plots raw values and an exponential moving average against
  the optimizer's training step. Switch between linear and signed-log axes.
  Each chart shows the latest value, EMA and range. The header also shows
  approximate KL, clipping, explained variance, action standard deviation,
  learning rate, recent rollout means and throughput when PPO reports them.
- **Policy network** traces the instantiated RGB encoder, host context,
  concatenated features, actor, critic and output heads. Click a layer to
  inspect shape, parameters, RMS and peak. The activity bar shows the fraction
  of nonzero values in the sampled forward output.
- **Reward** shows sampled step rewards, current components and accumulated
  episode components when available.

Optimizer events are emitted independently of the sampled activation feed.
To review an existing run, pass its JSONL log to the dashboard from the
repository root. Earlier logs expose their recorded metrics and activation
summary. Per-layer history requires a run created with the updated publisher.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$replay = 'PATH_TO_THE_RUN_DIRECTORY'
& $py -B simulation/mujoco/training/camera-manipulation/dashboard.py "$replay/dashboard.jsonl"
& $py -B -m pytest simulation/mujoco/tests/test_ppo_dashboard.py -q
~~~

~~~powershell
Set-Location 'F:\Users\EHD\Github\Atom\atom-chess'
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$r = 'simulation/mujoco/training/camera-manipulation/runs/qualification90-1794004012529819900'
$d = "$r/density-98ce29b538414c87aa7b210573f3556e"
$previous = "$d/center-clearance-watch-d54929be1816433d8f9ed76728c31dfc"
& $py -u -B simulation/mujoco/training/camera-manipulation/run.py --config "$d/center-clearance-v1.json" --camera-only --mode train --resume $previous --steps 2048 --episodes 1 --checkpoint-every 512 --watch --dashboard
~~~

The graph groups the actual forward activations by feature extractor, actor,
critic and output head. Brightness represents RMS activation magnitude in the
latest sampled forward pass. It does not show individual neurons or gradients.
Loss curves use PPO logger values and update after an optimization round.
Reward and its components are observed on rollout steps. Closing the dashboard
leaves training active. CSV export works with or without the dashboard.

| File | One row per | Contents |
|---|---|---|
| steps.csv | Environment step | Reward before PPO timeout bootstrapping, cumulative episode return, actions sent to the environment, phase, target, contact count, toppling, appearance and reward components |
| ppo_updates.csv | PPO optimization round | Update count, learning rate, policy loss, value loss, entropy loss, reported combined loss, KL, clipping, explained variance, exploration standard deviation, mean episode return and length, throughput |
| network.csv | Network module | Module name and type, linear input and output units or convolution channels, parameter count and trainable parameter count |

The PPO combined loss is the value reported by Stable Baselines3 for its
last minibatch in an optimization round. It is distinct from task reward.
Episode outcomes remain in episodes.jsonl. The CSV files are created in the
same fresh output directory and flushed as rows arrive. The dashboard also writes sampled activations and live status to dashboard.jsonl.
Earlier runs have only the telemetry captured when they were recorded.

To check the export, use --mode smoke --steps 64 with a compatible configuration.
Inspect steps.csv for 64 rows, ppo_updates.csv for two optimization rounds and
network.csv for both actor and critic layers. Initial evaluation and final
evaluation results are recorded separately in report.json.
