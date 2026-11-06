# P038 — Camera-guided residual manipulation

Status — the controlled one-piece training cycle is implemented and exercised.
The model remains an experimental MuJoCo prototype. Visual manipulation
confirmation and generalization remain open.

## Audited starting point

Branch ros2_simulation at dcf2dc1, with local P036/P037 work and earlier
playground/chess-monitor/CAD/training changes. All were preserved. No commit or
push was performed.

Inspected the P037 C ABI and Python adapter, CameraObservation, policy_observation,
the v3 VisualGraspEnv reset, training launcher and dependency pins. Inspected
MotionPlanner, CoordinateMapper, PhysicalTask, InverseKinematics, P015 exporter,
trajectory validation, Simulation, MotionController, SweptChecker, SceneCollision,
SceneFeedback and the actual joint/site/actuator geometry.

P037 really processes contiguous RGB through native acvision and returns
rectification, candidate labels and geometry. Its actor builder checks reference
orientation and freshness. v3 reset uses actual piece position for robot IK and
camera initialization. P038 has its own reset.

P015's exporter was a fixed E2/E3 demonstration. P038 adds a C ABI adapter around
the existing acmotion classes for configured physical endpoints and robot
geometry. The C++ planning and IK algorithms themselves are reused.

## Implemented files and responsibilities

| File | Responsibility |
|---|---|
| software/acmotion/runtime/motion_runtime.cpp | C ABI over actual MotionPlanner::planTask and InverseKinematics |
| simulation/mujoco/src/atom_mujoco/native_motion.py | Static model-to-SCARA mapping and native calls |
| simulation/mujoco/src/atom_mujoco/camera_manipulation_env.py | Gym reset/step, camera acquisition, phases, bounded residuals, safety, termination |
| simulation/mujoco/src/atom_mujoco/camera_reward.py | Privileged physical truth and decomposed rewards |
| simulation/mujoco/src/atom_mujoco/visual_verification.py | Multi-frame visual candidate states, independent of truth |
| simulation/mujoco/examples/prepare_camera_task.py | Exclusive derived one-piece scene and complete environment config |
| simulation/mujoco/examples/train_camera_manipulation.py | Baseline, PPO smoke/train, checkpoint, resume and independent evaluation |
| simulation/mujoco/tests/test_camera_manipulation.py | Native trajectory/FK, full transfer, isolation, rejection, perception-loss and reward regression |

The acmotion CMake option ACMOTION_NATIVE_RUNTIME defaults off. Existing targets
and the legacy environment/checkpoints are preserved.

## Actor boundary

The actor receives a copied, schema-validated dictionary of numeric arrays.
A byte round-trip detaches each payload from native/simulator-owned memory.

| Feature | Meaning |
|---|---|
| image | Native-acvision rectified RGB, resized to uint8 3x96x96 |
| task | Source/target column,row divided by seven |
| previous_action | Prior normalized residual proposal |
| commanded_joints | Five host command targets, in rad,m,rad,m,m |
| phase | Scheduled nominal command phase, rather than a sensed task assertion |
| perception_valid | Explicit observable validity mask |

There is no model/data/body/contact/reward argument to the actor. SimulatorTruth
is available only in the physics/controller, collision supervisor and independent
RewardEvaluator. The reward/info channel contains privileged diagnostics and is
never appended to actor features. Tests give two different simulator states the
same images and command history and verify identical actor payload bytes.

The reset uses the configured initial arm command and camera. It resets the
piece to the explicit fixture's initial position and holds the configured arm
command while physics settles. It never computes the starting robot pose or
camera lookat from the current piece pose.

## Nominal planner, geometry and units

The initial fixture has one white pawn, source e4 and target e5. Other free piece
bodies are omitted only from the new derived fixture. Original CAD, robot,
gripper, board and piece dimensions remain preserved.

The adapter derives shoulder position, link lengths, second-link angle offset,
neutral tool height, finger limits and joint limits from static model kinematics.
It verifies the derived IK mapping against MuJoCo FK on explicit robot poses.
For this model the derived planar lengths are 220 mm and about 144.539 mm.
The neutral tool height is 17 mm, shoulder XY is (40,0) mm.

Configured square geometry supplies nominal endpoints. Board homography supplies
the image rectification, separately from these metric scene calibrations.

C++ MotionPlanner creates eight phases.

1. APPROACH_SOURCE
2. LOWER_TO_SOURCE
3. GRASP_PIECE
4. LIFT_PIECE
5. APPROACH_TARGET
6. LOWER_TO_TARGET
7. RELEASE_PIECE
8. RETRACT

C++ poses use millimetres. Python converts them once to world metres.
The native IK bridge maps robot-world targets into the existing two-revolute
SCARA model and converts solved targets back to the five simulation joints.
The auxiliary C++ J3 is not actuated by this simulation profile. Its validation
bounds are derived from J1/J2 limits. This is the current position-only model.

Grasp height comes from the selected model stem proxy and the existing grasp
offset convention. Support height comes from board collision geometry and the
piece bottom. Open/closed jaw targets reuse pregrasp_opening and actual pad/stem
dimensions. Nominal travel height is grasp height plus two proxy piece heights
and one full pad thickness. This is an explicit experimental geometry rule,
subsequently checked by swept collision preflight.

## Residual action semantics

Action is float32 [delta_x,delta_y,delta_z,gripper_delta], each normalized to [-1,1].
XYZ offsets are in MuJoCo world axes, in metres after scaling. Gripper offset
is a coupled slide displacement in metres. Each proposal is relative to the
current nominal waypoint. Residuals never accumulate across steps.

Experimental bounds are derived from model proxy dimensions.

- XY is min(stem radius / 3, square-to-base radial clearance / 2).
- Z is stem proxy half-height / 4.
- Jaw slide is min(stem radius / 6, total finger travel / 10).

For this pawn these bounds are approximately [2,2,2.25,1] mm.
The control interval is five existing 20 ms controller updates, thus 100 ms of
simulated time. The joint command is additionally rate-limited by existing
joint velocity limits. Phase advancement follows commanded progress plus ten
dwell intervals, independently of oracle grasp signals.

A complete nominal swept path is checked on reset. Each proposed segment is
checked again from actual simulated joint state before actuator execution.
The supervisor reuses SweptChecker/SceneCollision and includes a carried-piece
transform in scratch collision data. It never teleports the live held piece.
Intended fingertip-piece contacts and phase-specific supports are explicit.
Runtime unexpected contacts can terminate the episode. Contact proxies and the
nominal joint-linear sweep remain experimental approximations.

Invalid actions, unreachable targets and unresolved/colliding segments terminate
before those commands reach physics. The agent cannot bypass this supervisor
or mutate logical chess state.

## Reward and termination

RewardEvaluator reads body poses, velocities, contacts and tool position only
for reward and evaluation. It measures bilateral grip, lift, transport, supported
placement, release, upright orientation and stability.

Reward terms are configured and logged. The current initial configuration uses
event rewards grasp=2, lift=3, transport=2, placement=3 and success=10,
failure=-5, time=-.01 and action squared cost=-.001. Approach shaping uses a
bounded tool-to-piece distance potential scaled by proxy piece height, weight .2.
Each event is paid once per episode to prevent repeated-contact reward farming.
Per-step and cumulative component sums are reported.

Success requires prior grasp/lift/transport events, released stable placement
inside the target clearance, upright/support conditions and completed retreat.
Placing a piece at the destination without the preceding grasp/lift evidence
cannot succeed. Existing SceneFeedback experimental stability/upright thresholds
are reused. Target radial tolerance derives from square half-width minus piece
base radius. Stable release requires five observations.

Explicit failure categories include INVALID_ACTION, INVALID_RESIDUAL,
UNSAFE_RESIDUAL, COLLISION, PIECE_LOST, GRASP_FAILED, GRIP_LOST, PLACEMENT_FAILED,
PERCEPTION_FAILED and TIME_LIMIT. Physics/native processing exceptions produce
a launcher failure.json and stop that run. They do not create success.

Perception loss returns a zero-image terminal observation with perception_valid=0.
Missing geometry never becomes an invented piece position. A perception failure
also cancels any simultaneous success reward.

The first fixture contains exactly one piece. Bystander disturbance testing
requires a later multipiece fixture and evaluator extension.

## Multi-frame visual evidence

VisualVerification consumes actual native candidate cells and ordered frame
sequences. It reports UNKNOWN, SOURCE_CANDIDATE, SOURCE_APPARENTLY_ABSENT,
TARGET_CANDIDATE and TARGET_TEMPORALLY_PRESENT_CANDIDATE. Repeated identical
sequence numbers are rejected. Three distinct matching frames are required for
temporal candidate states.

Native heuristics can mistake occlusion for absence. Disappearance alone cannot
establish out-of-plane transport or grip. In measured episodes the final visual
state was SOURCE_APPARENTLY_ABSENT and visual_confirmed remained false.
Physical oracle success is therefore reported separately. This is the explicit
remaining P038-E limitation permitted by the requested staged implementation.

## Build and prepare an independent fixture

Run PowerShell from the repository root.

~~~powershell
cmake -S . -B build/p038-core -G 'Visual Studio 18 2026' -A x64 -DOpenCV_DIR=D:/opencv/build/x64/vc16/lib -DBUILD_TESTING=OFF -DACCHESS_BUILD_VIEWER=OFF -DACVISION_NATIVE_RUNTIME=ON -DACMOTION_NATIVE_RUNTIME=ON
cmake --build build/p038-core --config Release --target motion_runtime acvision_runtime

& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/prepare_camera_task.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --reference-scene simulation/mujoco/runs/p035-steep-relayout/reference-scene.xml --layout docs/camera-rl/evidence-p035/high-camera-layout.json --output simulation/mujoco/runs/p038-single-piece
~~~

That fixture already exists in this workspace. Use another --output for a new
fixture. The preparer copies referenced assets and writes model.xml,
manifest.json, reference-layout.json and environment.json with hashes.
The generated configuration includes explicit camera, initial robot command,
piece identity, source/target, control frequency, reward weights and dependency
paths. Physical parameters are those recorded in the copied model/manifest.
The environment derives aperture and geometric parameters from those assets.
The preparer's --piece, --source and --target configure new fixed scenarios.

## Run a nominal episode or watch simulation

~~~powershell
$config = 'simulation/mujoco/runs/p038-single-piece/environment.json'
$run = Join-Path simulation/mujoco/runs ('camera-baseline-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/train_camera_manipulation.py --config $config --output $run --mode baseline --episodes 1 --watch
~~~

--watch uses MuJoCo's passive viewer. The executed validation runs were headless.
GUI viewing has an independent window and does not supply actor observations.

## Smoke test, training, resume and evaluation

~~~powershell
$config = 'simulation/mujoco/runs/p038-single-piece/environment.json'

$smoke = Join-Path simulation/mujoco/runs ('camera-smoke-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/train_camera_manipulation.py --config $config --output $smoke --mode smoke --steps 128 --episodes 1 --device cpu

$training = Join-Path simulation/mujoco/runs ('camera-train-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/train_camera_manipulation.py --config $config --output $training --mode train --steps 100000 --episodes 3 --device cuda

$resumed = Join-Path simulation/mujoco/runs ('camera-resume-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/train_camera_manipulation.py --config $config --output $resumed --mode train --resume $smoke --steps 128 --episodes 1 --device cpu

$evaluation = Join-Path simulation/mujoco/runs ('camera-eval-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/train_camera_manipulation.py --config $config --output $evaluation --mode evaluate --checkpoint simulation/mujoco/runs/p038-smoke-final/policy.zip --episodes 2 --device cpu --watch
~~~

The 100000-step command is available for user execution. Only short smoke/resume
runs were executed during implementation. PPO uses MultiInputPolicy, rollout 32,
batch 32, two epochs, learning rate 3e-4 and configured seeds. The actor consumes
P037 visual/task/history features and the explicit perception-valid mask.
Training workers are currently single-process. The older v3 worker launcher is
separate and does not select this environment.

Outputs include run.json, report.json, policy.zip, periodic checkpoint-N.zip and
episodes.jsonl when episodes finish. Reports include success/grasp/placement/
failure rates, collisions, duration, return, ending reason and reward decomposition.
Resume verifies the previous environment signature and checkpoint hash, then
restores PPO optimizer and timestep count. Source or scene changes require an
explicit new run instead of silently resuming incompatible state.

## Executed results

PyTorch 2.14.1+cu130, Gymnasium 1.4.0, Stable-Baselines3 2.9.2,
MuJoCo 3.17.0 and OpenCV 4.12.0. CPU was used for the short checks.

| Run | Result |
|---|---|
| Nominal zero residual | Full transfer and retreat in 92 steps, zero unexpected contacts |
| p038-smoke-final | 128 PPO steps, weight hash changed, one complete training episode |
| Reloaded smoke checkpoint | One evaluated transfer succeeded, zero unexpected contacts |
| p038-resume-check | Restored 128-step policy, trained 32 more steps, total 160 |
| p038-evaluation-check | Independent evaluation of saved smoke policy, 2/2 physical successes and 2/2 nominal successes |

Both nominal and residual policies succeeded in this fixed scene. The sample
does not demonstrate an RL advantage or generalization. Evaluation seeds differ
from the training seed but the scenario has no domain randomization yet.
Final physical placement error was about .35–.36 mm in this simulated fixture.
Visual confirmation remained false throughout these final reports.

Raw runs and checkpoints are preserved in simulation/mujoco/runs. The short
training verified reset, inference, bounded action, collision supervision,
actual physics, reward, termination, optimizer updates, checkpoint save/reload,
independent evaluation and resume.

## Tests and next functional work

Set the environment fixture path before running the P038 tests.

~~~powershell
$env:P038_CONFIG = (Resolve-Path simulation/mujoco/runs/p038-single-piece/environment.json).Path
$env:ACVISION_RUNTIME_DLL = (Resolve-Path build/p038-core/bin/Release/acvision_runtime.dll).Path
$env:ACVISION_PERCEPTION_EXE = (Resolve-Path build/p032-contract/bin/Release/perception_image.exe).Path
& simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_camera_manipulation.py simulation/mujoco/tests/test_native_runtime.py simulation/mujoco/tests/test_native_perception.py -q -p no:cacheprovider
~~~

Tests cover exact native reuse, full zero-residual transfer, two-world actor
isolation, invalid-action rejection before physics, supervisor rejection,
masked perception termination, reward anti-shortcut and distinct-frame visual
evidence. The full related Python suite passed 31 tests.

Next, improve multi-frame target/gripper evidence and introduce one justified
within-square position variation at a time to test whether residual learning
uses visual feedback. Robot/contact physics, TCP and physical calibration remain
experimental. Capture/graveyard tasks and the full chess loop are outside this
first one-piece environment.

See [ADR P038](../adrs/P038-camera-guided-residual-environment.md).

## Preserved evidence

See [smoke results](evidence-p038/smoke-report.json), [resume results](evidence-p038/resume-report.json), [independent evaluation](evidence-p038/evaluation-report.json) and [validation](evidence-p038/validation.json).

## Newly confirmed wrist-axis gap

The user confirmed that the physical gripper rotates 360 degrees about its fixed arm mounting point. The current P038 fixture has J1/Z/J2 and coupled fingers, with no wrist actuator. Its results and checkpoints qualify this reduced prototype only. The next robot-model revision must extract the mounting pivot/frame from CAD and update joint order, kinematics, supervision and actor command schema.
