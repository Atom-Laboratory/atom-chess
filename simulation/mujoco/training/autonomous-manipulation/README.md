# Autonomous visual manipulation experiment

This runner is the free temporal comparison experiment. The recommended next
deployment architecture and its planner/policy handoff are documented in the
[hybrid motion guide](../../../../docs/camera-rl/hybrid-motion-learning.md).

## Current version and first experiment

Environment version 3 uses a dedicated scene reset, camera-estimated source
context, logical kind/color conditioning and normalized command history.
Policy version 2 normalizes CNN features before actor/critic fusion. Read the
[current audit](../../../../docs/camera-rl/autonomous-multi-object-audit.md),
[reach curriculum decision](../../../docs/adrs/S025-autonomous-reach-curriculum.md)
and [feature normalization decision](../../../docs/adrs/S026-normalize-autonomous-visual-features.md).

The native MuJoCo Watch opens by default and stays open after results are
saved. Use `--headless` to explicitly disable visualization. `--watch` selects
the three-panel camera viewer. Add `--dashboard` independently to display
actual network activations, losses, rewards and physical feedback. GPU
training defaults to CUDA and reports a clear error if it is unavailable.
Use `--device cpu` for an explicit CPU experiment.

From the repository root in Windows PowerShell, prepare a fresh isolated
pawn curriculum using the generated full-board source fixture below.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$area = 'simulation/mujoco/training/autonomous-manipulation'
$source = 'simulation/mujoco/training/camera-manipulation/runs/pawn-e2-e4-vision-fen-v1/environment.json'
$fixture = Join-Path "$area/runs" ('reach-pawn-' + [guid]::NewGuid().ToString('N'))
& $py -B "$area/prepare.py" --config $source --output $fixture --isolated
$config = Join-Path $fixture 'environment.json'
& $py -u -B "$area/run.py" --config $config --objective reach `
  --steps 1024 --horizon 48 --episodes 8 --evaluation-seed 910000 `
  --rollout-steps 128 --batch-size 64 --epochs 5 `
  --learning-rate 0.0003 --target-kl 0.03 --ent-coef 0.005 `
  --checkpoint-every 256 --evaluate-before --dashboard
~~~

The source configuration and compiled native libraries must exist. The
[camera/FEN preparation guide](../camera-manipulation/README.md#board-state-and-rgb-localization-for-the-full-board-pawn)
recreates that full-board source. Every launcher prints its fresh output
directory. Keep `$config` assigned in the same PowerShell session. Paths
above are relative to the repository root.

Preparation retains the source robot, piece, gravity, collider and camera
properties. `--isolated` retains only the selected piece and derives matching
logical FEN. Omit it for the full-board fixture. The curriculum samples
collision-checked initial robot configurations two through three square
widths from the camera-estimated source, with varying wrist/elbow choices.
This teleports the simulated robot during initialization. Executing a safe
physical route from park to these configurations requires separate planning
qualification. The actor receives no successful trajectory or grasp height.

`reach` currently means mean fingertip clearance at most one square width,
35 mm in the supplied fixture. `grasp` requires bilateral contact and a
settled piece. `lift` additionally requires stable upward travel exceeding
one collision-model piece height. Watch shows the objective and physical
grip/lift separately. A reach result approves approach only.

Edit the prepared `environment.json` to change `autonomous.start_radius_squares`
or `autonomous.reach_distance_squares`, or pass the corresponding options to
`prepare.py`. `--parked` prepares the original parked initial condition.
Changing difficulty or success thresholds requires separate evaluation.
The initial near-start experiment and full-board manipulation have different
acceptance gates. Longer training is qualified only after measured held-out
improvement and stable resets on the named stage.

## Device diagnostic and outputs

~~~powershell
& $py -B "$area/diagnostics.py" --config $config --batch-size 64
~~~

This bounded diagnostic compares CPU/CUDA forward/backward/Adam updates on
the actual policy architecture. It verifies model/input/gradient/optimizer
devices, finite updates and policy/optimizer archive reload. Its report and
CSV distinguish neural update throughput from full-environment collection.

Training outputs include `run.json`, `report.json`, optional `baseline.json`,
`decisions.jsonl`, `steps.csv`, `performance.csv`, `ppo_updates.csv`,
`network.csv`, `hardware.jsonl`, checkpoint ZIPs with SHA-256 sidecars and
final RGB/rectified images. `--dashboard` additionally persists
`dashboard.jsonl`. Failure records include traceback and an attempted
`interrupted-policy.zip` save. Historical outputs are preserved.

To continue compatible weights, choose a completed run or verified checkpoint.

~~~powershell
$previous = 'PATH_TO_COMPLETED_RUN'
& $py -u -B "$area/run.py" --config $config --objective reach `
  --warm-start $previous --steps 1024 --horizon 48 --episodes 8 --dashboard
# Intermediate or interrupted recovery, using its .sha256 sidecar and run.json
& $py -u -B "$area/run.py" --config $config --objective reach `
  --warm-start-checkpoint "$previous/checkpoint-256.zip" --steps 1024 --dashboard
# Evaluation of the saved policy without optimization
& $py -u -B "$area/run.py" --config $config --objective reach `
  --warm-start $previous --evaluate-only --horizon 48 --episodes 24 --dashboard
~~~

Warm start verifies environment version, policy version, spaces and archive
hash, then copies weights into a fresh optimizer. Exact interrupted process
resumption is a separate capability. The previous unnormalized architecture
and residual archives require their original implementations.

## Regression checks

~~~powershell
$env:ATOM_AUTONOMOUS_CONFIG = (Resolve-Path $source).Path
& $py -B -m pytest -p no:cacheprovider `
  simulation/mujoco/tests/test_autonomous_manipulation.py `
  simulation/mujoco/tests/test_ppo_dashboard.py -q
~~~

Checks include policy isolation, reward signs, displacement penalties,
correct physical primitive heights, safe randomized starts, rejection without
scene mutation, action effects, normalized visual features and finite gradients.

## Historical version 2 prototype

The following notes record the initial temporal-action implementation and
its limitations before the version 3 scene and policy normalization changes.

This experimental runner learns continuous temporal commands without the
eight manipulation waypoints used by P038 residual PPO. The first increment
implements reach, bilateral-contact and stable-lift objectives. It uses the
same physical fixture and AC:Vision image bridge as the full-board P038
experiment. Physical success and visual confirmation are logged separately.
Transport, placement and physical recovery require subsequent qualification.

Read the [research audit and protocol](../../../../docs/camera-rl/approach-strategy-study.md)
and [ADR S022](../../../docs/adrs/S022-autonomous-temporal-actions.md).
The [P038 residual runner](../camera-manipulation/README.md), interactive
Playground and legacy v3 pixel training remain separate experiments.

## Prepare and run

Use Windows PowerShell from the repository root. Install the MuJoCo RL extra
and native libraries with the [module guide](../../README.md). Prepare the
full-board wrist environment using the [camera/FEN workflow](../camera-manipulation/README.md#board-state-and-rgb-localization-for-the-full-board-pawn).
The configuration requires an oriented board reference, calibrated RGB
localization, wrist limits, and simulated contact/displacement supervision.
The path below refers to a generated local fixture.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$config = 'simulation/mujoco/training/camera-manipulation/runs/pawn-e2-e4-vision-fen-v1/environment.json'
$launcher = 'simulation/mujoco/training/autonomous-manipulation/run.py'
& $py -u -B $launcher --config $config --objective reach --steps 128 --horizon 32 --episodes 3 --watch
~~~

Omit --watch for a headless run. Add --show-colliders to the Watch for diagnostic
geometry. This changes visualization only. --horizon limits policy decisions
per episode. This 128-decision pilot tests action execution. A manipulation
qualification needs a separately justified horizon and a frozen evaluation
protocol. --seed seeds training. --evaluation-seed starts a disjoint fixed seed
range. --stochastic-evaluation samples actions instead of using actor means.
Each invocation creates a fresh directory under this example's runs folder.
Use --output to select another fresh path.

For an interactive 3D window use --watch-native in place of --watch.
It displays a private copy of the live simulation state using MuJoCo's
native viewer. It supports orbit and zoom without sending scene edits to
training. The three-panel Watch publishes diagnostic images at up to five
updates per second. Both displays can repeat a state while the trainer
validates a command.
Add `--keep-watch-open` with `--watch-native` to keep the final 3D frame
visible after the report has been saved. Close MuJoCo to exit the launcher.

PPO defaults to CPU. Set --device cuda to use a compatible NVIDIA GPU for
policy inference and optimization, or --device auto to let PyTorch select
the device. The chosen device is recorded in run.json. MuJoCo's OpenGL
renderer selects its graphics adapter independently. Physics, native
perception and collision checks in this workflow run on the CPU.

The Watch displays actual simulated geometry, the actor camera frame, native
rectification, requested parameters, validation outcome, actual measured TCP
trail, reward, episode and training progress. Frames are throttled and
replace a single latest snapshot in the output directory. A rejected choice leaves the rendered
robot at its actual pose. A source image remains labeled by its observation
sequence while a temporal action executes. Closing the Watch allows headless
training to continue. The window keeps the last snapshot after training.
Its inspection camera is separate from the actor camera.

## Actor contract

The input contains two consecutive rectified RGB frames in six channels,
source/destination coordinates, two commanded-joint vectors, the previous
seven controls, a perception validity flag and the one-hot objective.
Commanded joints are host memory. The actor receives no contacts, true
object position, true joint state, model object or state-query callback.
There is no autonomous physical phase derived from oracle feedback in the
observation.

| Action | Interpretation and units |
| --- | --- |
| 0–2 | Cartesian velocity, m/s, scaled by the planar link lengths and joint speed limits or the Z speed limit |
| 3 | Wrist angular velocity, rad/s, scaled by the model wrist speed |
| 4 | Finger slide velocity, m/s, scaled by the coupled-finger speed |
| 5 | Elbow branch. Keep the current branch between −0.5 and +0.5, select up at or below −0.5 and down at or above +0.5 |
| 6 | Persistent duration from one control interval through the configured dwell count |

The action integrates from the TCP predicted by static forward kinematics
at the last commanded joints. Its displacement accumulates across decisions.
Thus pickup height, wrist orientation, path and timing are discoverable
through successive actions. A duration is selected once per action, rather
than sampled again at every physics frame. This is a first temporal-control
prototype. Learned high-level options and option termination remain proposed.

AC:Motion solves the requested Cartesian pose on the selected branch and
checks reachability. Wrist and finger endpoints respect available travel.
For a kinematic or speed rejection, the adapter tries shorter increments
along the same requested direction. The first kinematically valid segment
goes through the collision check, and a collision rejection remains a
rejection. See the command scale and actual joint target in decisions.jsonl.
A separate simulator supervisor checks
joint limits, speed and conservative swept collision geometry, including a
rigid carried-object approximation when bilateral contact exists. Bounding
spheres prune only pairs certified beyond the motion bound. Unresolved
geometry is rejected. Accepted commands use synchronized joint interpolation
and the existing controller. Physics can deviate from a nominal sweep, so
substep contact/topple checks stop unexpected execution and require scene
reconciliation. The simulation supervisor uses privileged state internally.
Equivalent hardware safety requires an observed/calibrated scene model.

Preflight rejection leaves the physical scene unchanged and permits another
action. This constitutes a retry before contact. Physical retreat and recovery
after an uncertain grasp or disturbed piece are gated and terminate the
episode. Whole-object visual tracking during occlusion is still an open
perception limitation. A valid homography establishes board reference, and
does not prove grip, a visible piece or hardware-safe recovery.

## Feedback and evidence

Reward includes changes in distance from both pads to the selected piece's
geometry, one-time bilateral-contact and lift events, stable-hold success,
action cost, rejection cost and physical contact/displacement/topple costs.
Proximity is training-only oracle feedback. No preferred pickup height or
waypoint is rewarded. A no-motion decision has zero proximity improvement
and a time cost. A rejected collision has a depth-dependent cost. Bilateral
contact is a contact observation. Stable lift additionally requires upward
travel exceeding one model piece height and sustained low piece velocity.
The lift gate uses ten decisions in the current fixture and inherits the
existing settled-velocity tolerances.

The runner initializes fresh PPO weights with 32 rollout decisions,
32 minibatch samples, two epochs and initial action standard deviation 0.4.
The action/observation semantics differ
from archived residual policies. Their weights remain baseline artifacts.
Discount is initially per policy decision, so the chosen variable duration
is a modeling limitation for a future semi-Markov comparison. SAC and
recurrent PPO are documented alternatives. No comparative performance
claim is established by this implementation.

Curriculum objectives share the same observation and action contract. After
qualifying an objective, use --warm-start with that completed autonomous run
to transfer weights to the next objective with a fresh optimizer. The
launcher checks the archive hash and policy spaces and records lineage.
This prototype accepts reach, grasp and lift goals. A residual checkpoint
has different input and output semantics and requires its own comparison.

Outputs include run.json with configuration and source/model/library hashes,
decisions.jsonl with choices and validation, steps.csv, ppo_updates.csv,
network.csv, policy.zip, optional intermediate checkpoints, report.json with
separate evaluation seeds, and final camera images. Requested diversity bins
use one square of XYZ displacement and 45° wrist intervals plus elbow sign.
Accepted bins are counted independently. Bin counts establish coverage of
requests, not learned successful strategies.

## Tests

~~~powershell
$env:ATOM_AUTONOMOUS_CONFIG = (Resolve-Path $config).Path
& $py -B -m pytest -p no:cacheprovider simulation/mujoco/tests/test_autonomous_manipulation.py -q
~~~

The integration test changes hidden physical state while keeping image and
host history fixed, checks unchanged actor inputs, rejects invalid and
colliding choices without moving the live scene, and tests perception-loss
termination. Tests require the generated native fixture when the environment
variable is present. A short trained/evaluated run validates data flow,
serialization and supervision; task success requires independent held-out
experiments with sufficient episode duration.
