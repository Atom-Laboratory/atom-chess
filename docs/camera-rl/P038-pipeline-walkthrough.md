# P038 — Read the running pipeline from entry point to weight update

This guide traces the controlled camera-guided environment actually used by
p038-smoke-final. Read it alongside [the execution guide](P038-camera-guided-manipulation.md).

## 1. Start at the launcher

Open [train_camera_manipulation.py](../../simulation/mujoco/training/camera-manipulation/run.py).
The main function parses --config/--mode, creates CameraManipulationEnv,
records provenance, evaluates the zero-residual baseline, constructs PPO and
calls policy.learn. It later saves policy.zip, loads another policy instance
and evaluates it. Resume loads the saved PPO optimizer and timestep state.

The entry point is main at the bottom of this file. The configuration used
by the smoke run is
simulation/mujoco/assets/bundles/p038-single-piece/environment.json.
The corresponding captured run.json is archived in
[evidence-p038/smoke-run.json](evidence-p038/smoke-run.json).

## 2. Where the scene and task come from

[prepare_camera_task.py](../../simulation/mujoco/examples/prepare_camera_task/run.py)
creates a new one-piece fixture from preserved model/marker-scene assets.
It writes model.xml, manifest.json, reference-layout.json and environment.json.

The current environment config supplies the bundle, vision/motion library paths,
marker layout, selected physical piece, source e4, destination e5, explicit
initial arm command, fixed camera and reward weights. This training task is
supplied by the scenario configuration. The full chess-game task adapter is a
separate integration.

The fixture model.xml defines meshes, bodies, joints, collision proxies,
actuators, gravity, friction and lighting. Its manifest records dimensions,
joint names, ranges, velocities and asset identities.
[backend.py](../../simulation/mujoco/src/atom_mujoco/backend.py) checks those
identities and loads MjModel/MjData. The reset restores the explicit fixture,
holds the configured arm command and lets physics settle. Arm/camera setup
is independent of the actual current piece position.

## 3. Where each camera image comes from

Open [camera_manipulation_env.py](../../simulation/mujoco/src/atom_mujoco/camera_manipulation_env.py).
Its constructor creates a mujoco.Renderer with the configured width/height.
It configures one free MjvCamera using lookat, distance, azimuth and elevation.
The render method updates the renderer from current simulation state and returns
an RGB uint8 HxWx3 array.

The current camera has 1920x1440 pixels, lookat [.245,0,.012] m, radial distance
1.05 m, azimuth 270 degrees and elevation -75 degrees.
Each step's image is freshly rendered from the resulting physical scene.
The render array is passed to NativeVision.observe from _observation.
The P038 hot path keeps frames in memory. Historical PNG captures are study
artifacts, rather than this environment's per-step image source.

## 4. What happens in acvision

Read [native_vision.py](../../simulation/mujoco/src/atom_mujoco/native_vision.py),
then [native_runtime.cpp](../../software/acvision/runtime/native_runtime.cpp),
then [perception_offline.hpp](../../software/acvision/apps/perception_offline.hpp).

Python checks RGB type/shape and calls the persistent C ABI through ctypes.
C++ converts RGB to BGR, then executes the same offline acvision orchestration.
The marker reference detector identifies four ArUco markers and refines their
corners. Its explicit layout supplies the destination correspondences.
The fitted image-to-board homography is validated and applied through the
existing Homography::warp. PieceDetector analyzes the 64 rectified cells.
The runtime returns RGB rectification, H, orientation, candidates and provenance.

The 800x800 rectified image is then resized to 96x96 for the policy.
Marker detection, projective fitting and deterministic planning are fixed
algorithms. Neural weights are updated in the PyTorch PPO policy.

## 5. Exactly where actor information originates

| Actor field | Source |
|---|---|
| image | MuJoCo RGB -> native acvision rectification -> 96x96 resize |
| task | Source and target in environment.json |
| previous_action | Previous normalized proposal emitted by the policy |
| commanded_joints | Host targets submitted to the controller |
| phase | Nominal trajectory command scheduler |
| perception_valid | Native geometry/orientation and frame freshness checks |

[camera_policy.py](../../simulation/mujoco/src/atom_mujoco/camera_policy.py)
builds the P037 PolicyObservation. The environment validates Gym shapes/dtypes,
copies values through bytes and returns detached numeric arrays.

Actual piece poses, measured joint state, contact signals, grip state and true
distances stay in simulator execution, collision supervision and reward evaluation.
They are not appended to actor features. Failed perception produces a terminal
observation with zero image and an explicit invalidity mask.

## 6. Where nominal robot movement comes from

Read [native_motion.py](../../simulation/mujoco/src/atom_mujoco/native_motion.py),
then [motion_runtime.cpp](../../software/acmotion/runtime/motion_runtime.cpp),
then [motion_planner.cpp](../../software/acmotion/src/motion_planner.cpp).

The simulation's static board calibration supplies the nominal square positions.
The native adapter calls the real C++ MotionPlanner::planTask, which expands the
transfer into eight labeled waypoints. This produces approach, descend, grasp,
lift, transport, descend at target, release and retreat.

The policy emits four corrections relative to the current waypoint.
XYZ corrections use world metres after scaling. The fourth correction adjusts
coupled jaw-slide opening. The environment calls the real C++ InverseKinematics
for the corrected point, applies rate and joint limits, then checks the segment
with SweptChecker before execution.

[collision.py](../../simulation/mujoco/src/atom_mujoco/collision.py) implements
the reused preflight and runtime collision checks.
[motion_controller.py](../../simulation/mujoco/src/atom_mujoco/motion_controller.py)
executes the accepted joint target with simulated gravity feedforward.
Simulation.advance advances MuJoCo dynamics. Piece movement follows contacts
and physics, including actual fingertip grip. Live execution never rigidly
attaches the piece with a teleport/weld shortcut.

Thus nominal Cartesian positions come from configured board/model geometry.
Camera images condition learned local corrections. The board homography remains
separate from robot-base metric calibration.

## 7. Where the reward comes from

[camera_reward.py](../../simulation/mujoco/src/atom_mujoco/camera_reward.py)
defines PhysicalTruth and RewardEvaluator. read extracts actual body position,
velocity, upright angle, TCP and fingertip contacts. evaluate computes
decomposed rewards and failure/success conditions.

Grasp, lift, transport and placement events are paid once. Completion requires
released stable placement, prior manipulation events and completed retreat.
Action cost and time cost apply along the way.

Reward and terminated/truncated values are learning signals. They are stored
with transitions for optimization, while the actor receives only the next
validated observation dictionary.
[visual_verification.py](../../simulation/mujoco/src/atom_mujoco/visual_verification.py)
separately tracks native multi-frame candidate states. In the current successful
smoke episodes visual_confirmed remains false. Physical success is oracle-scored.

## 8. What neural network was actually trained

The saved checkpoint uses Stable-Baselines3 2.9.2 MultiInputActorCriticPolicy.

- The RGB branch is NatureCNN with three convolutions and a 256-feature output.
- The other features provide 15 scalar values.
- CombinedExtractor concatenates those into 271 features.
- The actor has two 64-unit tanh layers, then four Gaussian action means and
  learned action standard deviations.
- The critic has its own two 64-unit tanh layers, then one predicted state value.
- Input uint8 image values are normalized by the SB3 image preprocessing.
- The feature extractor is shared by actor and critic in this configuration.

The actor proposes residuals during collection. The critic estimates expected
discounted return. The supervisor and physical controller handle each proposal
before simulation advances.

## 9. How weights change

The launcher calls PPO.learn. The installed SB3 implementation collects
32 transitions containing observation, action, reward, end flag, predicted
value and action log-probability. It computes returns and generalized advantage
estimates. Advantages describe how outcomes compare with the critic's prediction.

For two optimization epochs per rollout, PPO recomputes action probabilities
and values. Its clipped policy objective discourages excessively large changes
in action probability. A value MSE trains the critic.
For this checkpoint entropy coefficient is zero and value-loss coefficient is .5.

PyTorch computes gradients through the policy/value neural network.
Adam updates the network parameters at learning rate 3e-4 after gradient-norm
clipping at .5. Simulation outcomes supply stored experience for this loss.
The physics engine and C++ vision/planner do not participate in neural backprop.

The inspected checkpoint has gamma .99, GAE lambda .95, rollout size 32,
batch size 32, two epochs and clipping range .2. Its 128 transitions formed
four rollouts and eight optimizer-update epochs. The before/after network
weight hashes differ, as recorded in smoke-report.json.

To inspect installed library code locally, open these files.

- simulation/mujoco/.venv/Lib/site-packages/stable_baselines3/common/on_policy_algorithm.py,
  collect_rollouts, env.step and compute_returns_and_advantage.
- simulation/mujoco/.venv/Lib/site-packages/stable_baselines3/ppo/ppo.py,
  PPO.train, policy_loss, value_loss, loss.backward and optimizer.step.
- simulation/mujoco/.venv/Lib/site-packages/stable_baselines3/common/torch_layers.py,
  NatureCNN and CombinedExtractor.
- simulation/mujoco/.venv/Lib/site-packages/stable_baselines3/common/policies.py,
  MultiInputActorCriticPolicy.

These are installed dependencies for reading. Project-specific changes belong
in repository source and configuration.

## 10. Files to inspect after a run

| Artifact | What it answers |
|---|---|
| environment.json | Which scene, task, camera, reset and reward parameters? |
| run.json | Which source/assets/libraries, geometry and action bounds? |
| episodes.jsonl | Which episodes completed, why, and with what reward components? |
| report.json | Baseline/residual results, weight hashes, update count, reload status |
| policy.zip | Learned weights, policy metadata and optimizer state |
| checkpoint-N.zip | Periodic recoverable policy snapshots |
| failure.json | Why a run stopped unexpectedly |

The current fixed-scene smoke proves a working training loop. Baseline and
residual both succeed. It has yet to demonstrate visual generalization or a
benefit over the nominal trajectory.
