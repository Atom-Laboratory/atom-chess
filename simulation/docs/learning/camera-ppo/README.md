# Build ATOM's camera-guided PPO training from first principles

This is a reconstruction guide for the **P038 camera-guided residual policy**,
including the full-board wrist experiment and the three-tab PPO dashboard.
Work through it with one objective in mind. Given an image, a logical source
square and a destination square, build a system that can pick up the intended
piece and place it while disturbing the board as little as possible. You should
be able to replace each component independently and explain the evidence that
the replacement works.

| Start here if you want to | Section |
| --- | --- |
| Trace where each number comes from | [Follow one action](#1-follow-one-action) |
| Rebuild the camera and motion pipeline | [Perception and control](#2-reconstruct-perception-and-motion) |
| Read the network graph in the screenshot | [Network anatomy](#4-rebuild-the-network-in-the-dashboard) |
| Derive the weight update | [PPO mathematics](#5-derive-one-ppo-update) |
| Run and diagnose an experiment | [Operational laboratory](#7-run-and-diagnose-the-experiment) |
| Learn the prerequisite subjects in order | [Reconstruction roadmap](#8-reconstruction-roadmap) |
| Choose books, papers and implementations | [Annotated references](#9-annotated-references) |

## 1. Follow one action

The experimental task is a physical transfer such as E2 → E4. AC:Chess
supplies the move and pre-move FEN in the full-board fixture. FEN gives the
logical piece type and color on each occupied square. A centered square
coordinate is an initial geometric reference. The actual pickup offset comes
from the image. The fixture records a snapshot, so advancing a live game
requires a separate integration with AC:Chess. The interactive Playground,
legacy v3 lift/grasp curriculum and P038 launcher are distinct workflows.

~~~mermaid
flowchart LR
    Chess["AC:Chess: task and logical board"] --> Target["Source, destination and expected occupants"]
    Physics["MuJoCo physics"] --> RGB["Virtual RGB camera"]
    RGB --> Vision["AC:Vision: oriented rectification"]
    Vision --> Localize["RGB source offset"]
    Target --> Localize
    Localize --> Nominal["AC:Motion nominal waypoints"]
    Vision --> Obs["Actor observation"]
    Target --> Obs
    Commands["Command history and phase"] --> Obs
    Obs --> Policy["CNN + actor and critic"]
    Policy --> Residual["Bounded correction"]
    Nominal --> Control["IK and rate-limited command"]
    Residual --> Control
    Control --> Physics
    Control --> Commands
    Physics -->|training supervision| Reward["Contact, displacement and toppling costs"]
    Vision -->|task verification| Reward
    Reward --> Update["Rollout buffer, GAE and PPO update"]
    Policy --> Update
    Update --> Policy
~~~

Trace a single `step(a)` by keeping the following quantities separate.

| Quantity | Origin | Consumer |
| --- | --- | --- |
| FEN and source/destination | AC:Chess bridge, exported to the fixture | Task selection, localization and planner |
| Raw and rectified RGB, orientation and validity | Virtual camera and native AC:Vision | Localizer, policy input and visual verification |
| Source XY estimate | RGB registration at reset plus nominal square center | Nominal pickup path |
| Previous action, phase and commanded joints | Host control loop | Policy input |
| Static geometry, limits, TCP and board-to-base transform | Experimental calibration/model | Planning, IK and command bounds |
| True neighbor movement, contacts and tilts | MuJoCo physics | Training supervision and diagnostics |
| Gaussian mean and critic value | PPO forward pass | Action sampling and value estimation |

The trainer can compare an RGB estimate with a simulator pose in an offline
test. Keep that comparison outside the observation builder and the planner.
The physics backend still integrates joint state and uses actuator dynamics.
The actor sees **commanded joints**, which the host can remember on hardware.
Backlash, slip and a missed motor step can separate commands from actual
positions. This distinction matters even with a fixed arm and board.

### Read the code in execution order

| Question | Entry point |
| --- | --- |
| Which config, seed, checkpoint and run mode did I choose? | [Launcher and provenance](../../../mujoco/training/camera-manipulation/run.py) |
| How did E2 and E4 become a physical request? | [Chess Core bridge and FEN decoder](../../../mujoco/src/atom_mujoco/chess_commands.py) |
| Who acquires and rectifies RGB? | [Camera definition](../../../mujoco/src/atom_mujoco/virtual_camera.py) and [native vision adapter](../../../mujoco/src/atom_mujoco/native_vision.py) |
| Where does the source coordinate change? | [RGB localization](../../../mujoco/src/atom_mujoco/board_piece_localization.py) and `CameraOnlyEnv.reset` in the [camera environment](../../../mujoco/src/atom_mujoco/camera_only_env.py) |
| Where are nominal poses, IK and actuator commands produced? | [Motion adapter](../../../mujoco/src/atom_mujoco/native_motion.py), [controller](../../../mujoco/src/atom_mujoco/motion_controller.py) and [physics backend](../../../mujoco/src/atom_mujoco/backend.py) |
| What exactly enters the network? | [Observation builder](../../../mujoco/src/atom_mujoco/camera_policy.py) and [Gym spaces](../../../mujoco/src/atom_mujoco/camera_manipulation_env.py) |
| Where is reward computed and logged? | `CameraOnlyEnv.step`, [physics supervision](../../../mujoco/src/atom_mujoco/contact_supervision.py) and [CSV telemetry](../../../mujoco/training/camera-manipulation/telemetry.py) |
| Which code draws the live values? | [Publisher](../../../mujoco/training/camera-manipulation/dashboard_publisher.py), [dashboard](../../../mujoco/training/camera-manipulation/dashboard.py) and [progress reporter](../../../mujoco/training/camera-manipulation/run_progress.py) |

## 2. Reconstruct perception and motion

### From pixels to a pickup point

1. Acquire an RGB frame with a camera identity and timestamp. Keep the camera
   on its calibrated mount. Define the intrinsics, distortion model, board
   dimensions and the transform from board coordinates into robot-base
   coordinates. The camera-to-board correspondence and the board-to-base
   transform answer different questions.
2. Detect oriented ArUco corners and pair each measured image point with its
   known board-plane location. In homogeneous coordinates, a homography
   maps a pixel vector `[u, v, 1]` to a rectified vector proportional to
   `[x, y, 1]`. Divide by its third coordinate. A homography has eight
   degrees of freedom up to scale. Four points in general position suffice
   algebraically. Extra well-spread correspondences allow robust fitting
   and residual checks. Reject ambiguous orientation and validate on
   points excluded from the fit. [Homography tutorial](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html) · [ArUco documentation](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
3. Warp to the board-aligned image. AC:Vision produces an **800 × 800** board
   raster. Parse the FEN to identify expected occupied squares. Use an empty
   board RGB reference to form a foreground mask and a centered-piece RGB
   reference to estimate displacement. The current localizer searches
   small shifts by FFT cross-correlation and ranks them by mask intersection
   over union, `IoU = |A ∩ B| / |A ∪ B|`. It requires compatible references,
   enough foreground, a convincing peak and a peak inside the search range.
   A missing source estimate prevents motion. Occluded or ambiguous
   neighbors can remain unlocalized.
4. Convert the rectified shift to metric XY and add it to the nominal source
   square center. For a **35 mm** pitch and **100 px** per square, a measured
   `(+4, -3) px` image shift maps to `(+1.40, +1.05) mm` in the fixture's
   board axes. Pixel rows increase down, while board Y increases toward
   rank 8. Verify these signs on labeled points. Convert through the
   board-to-base calibration before commanding the tool.
5. Estimate the pickup height from the board plane, piece/grasp geometry
   and calibrated TCP. A homography is a planar mapping. The head of a
   standing piece and an airborne piece lie off that plane, so their
   projected pixels can shift with viewing angle. The centered appearance
   calibration limits this problem for small planar offsets. True 3D pose
   recovery requires additional geometric assumptions, measured
   correspondences, depth or multiple views. [Multiple View Geometry](https://www.robots.ox.ac.uk/~vgg/hzbook/)

The simulated calibration references are generated separately from the live
episode. On hardware, acquire those references from the actual camera.
Measure metric localization error as a function of square, piece, light,
occlusion and camera pose. Report median, 95th percentile and invalid-frame
rate separately. A tiny reprojection residual on the fitted marker corners
does not establish millimeter accuracy at the far side of the board.

### From pickup point to actuator command

The native planner generates eight nominal waypoints. Their sequence is
approach source, lower, grasp, lift, approach target, lower, release and
retract. The policy's displayed phase groups the first two as **APPROACH**.
After retract, the camera-only environment returns the arm to an inspection
pose to verify the destination and neighbors. These phases are part of the
controller. They are also inputs to the policy, which can learn different
corrections for grasp and transport.

For the wrist fixture, the five normalized action coordinates are
`(Δx, Δy, Δz, Δopening, Δwrist)`. For position, apply a phase waypoint
plus a scale times the action, component by component. Clip the opening to
joint bounds. The wrist command uses a nominal orientation and a bounded,
rate-limited offset. In the visual-qualification curriculum, the wrist
residual target is sampled at elevated approach and transport phase entry
and then held. Inspect the config and the applicable branch before assuming
that every action component changes the robot at every step.

The native IK solves for shoulder, elbow and Z with calibrated tool offsets.
A useful independent check is the planar two-link model, where
`x = L1 cos(q1) + L2 cos(q1 + q2)` and
`y = L1 sin(q1) + L2 sin(q1 + q2)` in the shoulder frame. Solve both
elbow branches, then reject solutions outside travel and velocity limits.
The actual adapter also accounts for the wrist-dependent offset of the
grasp center and converts between Python meters and native millimeters.
An IK solution establishes endpoint reachability. Evaluating the whole
swept volume is a separate collision test. [Modern Robotics](https://modernrobotics.northwestern.edu/)

An **environment step** consumes one action and applies several control
intervals. Each control interval can contain several physics substeps.
Before early stopping, simulated step duration is approximately
`model.opt.timestep × control_substeps × control_repeat`. Wall-clock
latency also includes RGB rendering, native vision, inference and optional
visualization. Compare policies by environment interactions and wall time
separately. A high training throughput says little about grasp quality.

### Build a physics test before using the full robot

Start with gravity, a plane, a free rigid piece and two actuated fingers.
For generalized coordinates, the mental model is
`M(q) qdd + bias(q, qd) = actuator_forces + J_contact(q)^T × contact_forces`.
Mass and inertia determine response to force and torque. The contact
Jacobian maps generalized velocities into local contact velocities, and
its transpose maps contact forces back into generalized forces. The solver
uses contact geometry, friction and constraint parameters to determine a
numerical response. The actual CAD appearance, collision geometry and
inertial model can differ. Inspect all three.

Run drop, slide and pinch experiments in isolation. In a symmetric
quasi-static pinch, a first-order check is whether the combined tangential
friction capacity `2 μ N` can support weight `m g`. Here `N` is the
normal force per finger. This scalar check omits grasp torque, acceleration,
contact patch changes and solver compliance. Measure what breaks when you
vary friction, contact geometry, finger stiffness and timestep independently.
Use the resulting tolerances to design a repeatable baseline before RL.
[MuJoCo modeling manual](https://mujoco.readthedocs.io/en/latest/modeling/)

## 3. Formulate the learning problem and the reward

Think of the simulator state as joint position and velocity, contact
configuration, board poses and other dynamics variables. The actor
observation is partial. A single RGB image and the last command can hide
piece velocity, an occluded object or internal gripper contact. PPO here
uses a feed-forward network, so the previous action supplies limited history.
If two situations need different responses but produce essentially the same
input, improve sensing or add a justified history mechanism before making
the network larger.

The reward is a scalar for a transition, while episode success is a separate
predicate. In the current camera-only environment the final verification
combines repeated visual source/destination candidates, the inspection
phase, neighbor appearance checks and, when enabled, upright silhouette
agreement. `grasp` and `lift` remain unverified in this path. A closing
command or a phase transition alone supplies no proof of a grasp or lift.
The legacy oracle-reward environment uses a different contract.

| Signal | How the camera/FEN fixture uses it |
| --- | --- |
| Time and action | `-0.01` per step and `-0.001 × sum(a²)` |
| Final visual success | `+10` after the visual predicate passes |
| Neighbor visual change | Appearance difference contributes a penalty at final inspection, and excess change can fail the episode |
| Non-target contact | Configured negative reward once per affected environment step, even if multiple contacts occur within it |
| Non-target displacement | Configured penalty per new millimeter of maximum excursion from the settled initial position, summed across neighbors after a 0.25 mm dead band |
| Toppling | Simulator supervision terminates on detected excessive tilt and applies a configured cost |
| Failure | Additional `-5`, including a horizon timeout recorded as `TIME_LIMIT` |

In the displacement rule, a neighbor moving 2.0 mm from origin incurs
1.75 billable millimeters. Returning to 1.0 mm charges zero extra. Moving
out to 3.0 mm charges another 1.0 mm. The cumulative charge is 2.75 billable
millimeters. This is a peak-excursion objective. Total path length would
penalize oscillation differently. Test this distinction before changing the
penalty. Neither the measured excursion nor the contact array is a policy
feature. They provide training signals and diagnostics.

For new grasp and lift rewards, design independent visual tests. A grasp
candidate could require persistence of the piece relative to the fingers
across a small lift. A lift candidate could require separation from the board
and co-motion across frames. An occluded frame should remain unknown.
Record the first transition that verifies each event so the agent cannot
farm a bonus by repeating it. Prototype positive and negative videos before
training. Potential-based shaping, `γ Φ(s_next) - Φ(s)`, is a special
construction with policy-invariance conditions. The contact and displacement
costs in this experiment intentionally change which outcomes are preferred.
[Policy invariance under reward transformations](https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf)

## 4. Rebuild the network in the dashboard

The pictured policy is SB3's **MultiInputPolicy**, a conventional CNN for
RGB plus two multilayer perceptrons for actor and critic. The CNN learns
image features. The actor turns fused features into an action distribution.
The critic turns the same features into an estimate of discounted return.
There is no attention or Transformer block in this architecture.

The observation builder passes a rectified RGB resize as uint8
`3 × 96 × 96`. SB3 scales the image to floating-point `[0,1]` before
the CNN. It also passes four normalized source/target file and rank
coordinates, five previous residuals, six commanded coordinates in the
wrist fixture, one phase index and one perception-valid flag. The phase
is represented by a scalar box in this policy. The actor does not receive
the entire FEN as a feature vector. AC:Chess and perception consume it
upstream. The camera validity flag is a status bit rather than a
confidence probability.

| Layer | Output | Trainable parameters |
| --- | --- | ---: |
| RGB input | `3 × 96 × 96` | 0 |
| Conv, kernel 8 × 8, stride 4, ReLU | `32 × 23 × 23` | 6,176 |
| Conv, kernel 4 × 4, stride 2, ReLU | `64 × 10 × 10` | 32,832 |
| Conv, kernel 3 × 3, stride 1, ReLU | `64 × 8 × 8` | 36,928 |
| Flatten and projection with ReLU | `4096 → 256` | 1,048,832 |
| Concatenate RGB and host features | `256 + 17 = 273` | 0 |
| Actor, Tanh hidden layers | `273 → 64 → 64` | 21,696 |
| Critic, Tanh hidden layers | `273 → 64 → 64` | 21,696 |
| Action mean head | `64 → 5` | 325 |
| State-value head | `64 → 1` | 65 |
| Learned action log standard deviations | `5` | 5 |
| **Total** | Wrist fixture pictured | **1,168,555** |

Compute the first row of learned layers yourself. The spatial output is
`floor((96 - 8) / 4) + 1 = 23`. Each of 32 filters has `3 × 8 × 8`
weights and one bias, so `32 × (192 + 1) = 6176`. Apply the same
formula to the other convolutions. The dense projection accounts for
about 90% of the parameters. Changing image resolution can change that
flatten size and invalidate old checkpoints. Validate the live policy
against `network.csv` instead of assuming every bundle has the wrist.
[Deep Learning, chapter 9](https://www.deeplearningbook.org/contents/convnets.html) · [SB3 PPO](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html)

The screenshot shows `1346/4096 steps` and **APPROACH**. The step count is
the current run's training budget progress and APPROACH is the manipulation
phase. Clicking Conv 32 reveals the shape, parameter count, RMS and peak.
RMS is `sqrt(mean(x²))` over that sampled output tensor. The activity bar
is its nonzero fraction. ReLU can produce exact zeros, while Tanh often
produces nonzero values almost everywhere. Thus **100% active** can coexist
with saturation and tiny gradients. An RMS near one after Tanh motivates
checking the fraction close to ±1 across frames. A forward snapshot shows
activations and says nothing directly about gradients, feature importance,
reward or policy quality.

For the action head, `μ(o)` is a vector of five Gaussian means. Exploration
samples from a diagonal Gaussian with learned `σ = exp(log_std)`. The mean
can be outside the environment's `[-1,1]` bounds. SB3 clips the command
sent to the environment for this policy, and its PPO objective uses the
sampled action and its log probability in the rollout buffer. The value
`V(o)` estimates the future discounted reward under the current policy.
It is neither a probability of success nor the reward just received.

## 5. Derive one PPO update

### Return, value and advantage

Define the return at step `t` as `G_t = r_t + γ r_(t+1) + γ² r_(t+2) + …`.
`V(o_t)` estimates its conditional mean. An advantage compares an action
with the policy's typical result at the current observation. Generalized
Advantage Estimation uses a sequence of temporal differences.

~~~text
δ_t = r_t + γ × m_t × V(o_(t+1)) − V(o_t)
A_t = δ_t + γ × λ × m_t × A_(t+1)
value_target_t = A_t + V_old(o_t)
~~~

Here `m_t` gates continuation at genuine terminal states. At a collection
boundary, bootstrap from the final value when the task continues. At a
time limit, bootstrap from the terminal observation when the wrapper
classifies the episode as truncated. Keep that observation distinct from the
next episode's reset frame. SB3 folds the time-limit bootstrap into its
rollout reward in this case. The step CSV records the environment reward
before that adjustment. `λ` controls how far TD errors propagate and trades
bias against variance. [GAE paper](https://arxiv.org/abs/1506.02438) · [Gymnasium time limits](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/)

Work a two-step example. Let `γ = .99`, `λ = .95`,
`V(o_0)=1`, `V(o_1)=2`, and rewards `(-.01, +10)` with a real
terminal transition at step 1. Then `δ_1=8`, `δ_0=.97`,
`A_1=8` and `A_0=.97 + .99 × .95 × 8 = 8.494`. The critic target
at step 0 is `9.494`. Change the final event to a truncation with a
nonzero final value and recalculate.

### Likelihood ratios and the clipped objective

The policy gradient follows from the log-derivative identity. For a
trajectory distribution `p_θ(τ)`, differentiating the expected return
uses `∇p_θ = p_θ ∇log p_θ`. If initial conditions and transition
dynamics do not depend directly on `θ`, the remaining terms are the
sum of action log-probability gradients along the trajectory. Subtract
an observation-dependent baseline to reduce variance. Its expected
contribution is zero because the action probabilities integrate to
one. GAE estimates the resulting advantage with temporal-difference
errors and adds a tunable bias–variance trade-off.

For a single Gaussian action dimension with fixed `σ`,
`∂ log π(a | μ, σ) / ∂ μ = (a - μ) / σ²`. A positive advantage pushes
the mean toward the sampled action when the surrogate is locally
unclipped. A negative advantage pushes it away. The direction of the
shift depends on the sample's position relative to the mean. This is
why the algorithm can learn without a labeled correct action.

Store the old log probability when collecting the action. During an
optimizer epoch, score the **same sampled action** under the current actor.

~~~text
ratio = exp(log π_new(a | o) − log π_old(a | o))
surrogate = min(ratio × A, clip(ratio, 1 − ε, 1 + ε) × A)
policy_loss = −mean(surrogate)
value_loss = mean((V_new(o) − value_target)²)
entropy_loss = −mean(entropy(π_new))
total_loss = policy_loss + vf_coef × value_loss + ent_coef × entropy_loss
~~~

SB3 normalizes advantages within the minibatch for this setup. With
`A=+2`, `ratio=1.5`, `ε=.2`, the surrogate contribution is
`min(3,2.4)=2.4`. Increasing the probability of that already favored
action earns no extra clipped gain in that region. With `A=-2` and
`ratio=.5`, compare `-1` and `-1.6`. This time the minimum is
`-1.6`. Check both signs in an implementation test.
[PPO paper](https://arxiv.org/abs/1707.06347) · [Spinning Up derivation](https://spinningup.openai.com/en/latest/algorithms/ppo.html)

Call backpropagation on the total loss. The critic error reaches the
critic and the shared CNN. The policy gradient reaches the actor,
action distribution and shared CNN. SB3 clips the global gradient norm
and Adam updates the weights using running gradient moments. A second
epoch uses the same stored rollout with the new weights and the same
old log probabilities. PPO is on-policy at rollout collection, with
limited reuse inside that update. It does not need to differentiate
through MuJoCo, ArUco detection or the native IK solver.

### Settings and counters to reproduce

| Parameter | Fresh P038 launcher | What changing it means |
| --- | --- | --- |
| Environments | One in this launcher | A vectorized design would collect from multiple environments and alter the update batch |
| `n_steps`, `batch_size`, `n_epochs` | 32, 32, 2 | A full rollout feeds one minibatch per epoch, usually two optimizer steps per rollout |
| Learning rate | `3e-4` | Adam's update scale |
| `gamma`, `gae_lambda` | `.99`, `.95` | Discount and temporal credit assignment |
| `clip_range`, `clip_range_vf` | `.2`, none | Policy ratio clipping and optional separate value clipping |
| `ent_coef`, `vf_coef` | `0`, `.5` | Relative weighting of entropy and value loss |
| `max_grad_norm` | `.5` | Global gradient norm cap |
| `--steps` | Requested new interactions | PPO finishes full rollouts, so 33 requested steps become 64 in this setup |
| `--episodes` | Evaluation episodes per comparison | Adds evaluation work and changes the evidence count. Training still collects rollouts up to its step budget |

Values set by the launcher and inherited defaults refer to SB3 2.9.2 in
the repository's RL extra. A loaded checkpoint can carry different
hyperparameters. Audit the runtime and checkpoint before reproducing
an experiment. A policy can take more than one rollout to finish a
single episode. A rollout boundary is a learning boundary and does not
necessarily reset the robot. [Pinned dependency specification](../../../mujoco/pyproject.toml) · [SB3 PPO parameters](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html)

## 6. Implement a minimal trainer yourself

Start with a two-action bandit and verify the expected reward analytically.
Then use a toy continuous task, such as reaching a one-dimensional target
with a bounded command, before replacing that environment with MuJoCo.
Write the following loop without using an SB3 optimizer or rollout buffer.
Using PyTorch automatic differentiation is enough to test your derivation.

~~~text
initialize actor, critic, optimizer and seeded environment
observation = env.reset()
repeat:
    collect K transitions with gradients disabled:
        mean, log_std, value = network(observation)
        sample raw action and store its old log probability
        applied_action = clip(raw_action, -1, 1)
        step the environment and store reward, observation and boundary flags
        bootstrap truncations from their final observation as designed
        reset only when the episode ends
    compute advantages and value targets backwards
    for each optimizer epoch:
        shuffle transition indices
        for each minibatch:
            recompute log probabilities and values from stored inputs
            compute ratio, clipped objective and value loss
            zero gradients, backpropagate, clip gradient norm, step Adam
    log the rollout and losses
    evaluate a frozen copy on seeds excluded from training
~~~

An implementation order for the network is `Conv2d → ReLU` three times,
then `Flatten → Linear(4096, 256) → ReLU`. Concatenate the 17 host
values with the 256 features along the final axis. Give the actor and
critic independent `Linear(273, 64) → Tanh → Linear(64, 64) → Tanh`
branches. Add the two output heads and a trainable five-element
`log_std` parameter. Use a diagonal Gaussian and sum log probabilities
across the five action dimensions to obtain one log probability per
transition. Verify batched shapes before touching the environment.

Build checks before changing hyperparameters.

1. Hand-calculate a two-step return and GAE with both a terminal and a
   truncated transition. Compare them with your buffer.
2. Check ratio = 1 before the first parameter update, to numerical
   tolerance, on fixed inputs and raw sampled actions.
3. Compare automatic differentiation with centered finite differences on
   a small network and a fixed batch. Avoid nondifferentiable clipping
   boundaries for this test. Check that actor and critic gradients reach
   the intended branches.
4. Log one raw sampled action and one applied action outside the bounds.
   Verify that training scores the same raw sample used to record the old
   log probability. Explain what repeated clipping does to effective
   exploration.
5. Keep the policy frozen and replay identical camera observations. Verify
   shape, dtype, preprocessing, action order and deterministic output after
   reloading. Change the image or goal and test which outputs change.
6. Implement a dummy environment with a sensor payload and an oracle
   payload. Deliberately mutate the oracle while holding the camera and
   host inputs fixed. The policy observation must stay identical while
   the training reward may change.

Use the single-file CleanRL implementation as a code-reading comparison,
then inspect SB3. Compare advantage normalization, action handling,
termination, optimizer defaults, initialization and metric aggregation.
Small implementation choices can change measured results.
[CleanRL paper](https://arxiv.org/abs/2111.08819) · [Implementation Matters in Deep Policy Gradients](https://arxiv.org/abs/2005.12729)

## 7. Run and diagnose the experiment

### Run the real pipeline

Use Windows PowerShell from the repository root. Install the RL Python
extra, build the native AC:Vision and AC:Motion libraries and prepare the
camera fixture before training. Follow the [MuJoCo setup](../../../mujoco/README.md)
and the [full-board camera/FEN workflow](../../../mujoco/training/camera-manipulation/README.md#board-state-and-rgb-localization-for-the-full-board-pawn).
Use the full-board pawn fixture for the pictured wrist policy. Older
bundles can have different policy dimensions. Replace the example
configuration path with your generated file. Each command automatically
creates a fresh run directory.

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$launcher = 'simulation/mujoco/training/camera-manipulation/run.py'
$config = 'simulation/mujoco/training/camera-manipulation/runs/pawn-e2-e4-vision-fen-v1/environment.json'
if (-not (Test-Path -LiteralPath $config)) {
    throw 'Set $config to the prepared full-board pawn environment.json'
}

# Measure the zero-residual controller first.
& $py -u -B $launcher --config $config --camera-only --mode baseline --episodes 1 --watch

# Check the learning loop and dashboard with one full rollout.
& $py -u -B $launcher --config $config --camera-only --mode smoke --steps 32 --episodes 1 --watch --dashboard

# Train a freshly initialized policy. Omit viewer flags for throughput trials.
& $py -u -B $launcher --config $config --camera-only --mode train --steps 2048 --episodes 1 --checkpoint-every 512 --watch --dashboard
~~~

Verify the printed output directory. `run.json` records the environment
identity, configuration and lineage. `report.json` separates baseline and
policy evaluation and records weight digests. `steps.csv` and
`episodes.jsonl` explain rewards and failure events. `ppo_updates.csv`
describes optimizer rounds, `network.csv` describes modules,
`dashboard.jsonl` records live telemetry, and RGB/homography images
record what was available to perception. Checkpoints store learned weights
and associated training state. Keep original results and write new runs
into fresh directories.

- Use `--resume $priorRun` for a compatible completed run when preserving
  the optimizer and lifetime step counter. The displayed progress counts
  the new steps. Environment and checkpoint identities are checked.
- Use `--warm-start $priorRun` or
  `--warm-start-checkpoint $checkpointZip` to copy compatible weights
  into a fresh optimizer. An intermediate archive belongs in its original
  run directory. Use `--checkpoint-sha256` when pinning that archive.
- Use `--mode evaluate --checkpoint $checkpointZip` for frozen evaluation.
  The launcher also runs its deterministic baseline for comparison. The
  same source run and versioned test inputs make that comparison traceable.

### Read the screen and the files together

| Screen value | Meaning | What to inspect next |
| --- | --- | --- |
| Training steps and phase | Progress in this execution and current manipulation phase | Terminal and `dashboard.jsonl` for baseline, training and final evaluation boundaries |
| Total loss | Combined objective reported from the last minibatch | Actor and critic loss separately. A large value loss can dominate the total |
| Policy loss | Mean clipped policy objective with a negative sign for minimization | Approximate KL and clipping fraction. Values near zero alone can be normal after advantage normalization |
| Value loss | Mean squared critic prediction error against rollout targets | Reward scale, outliers, failure timing and explained variance |
| Entropy loss and action σ | Negative entropy of the policy and its exploration scale | Fraction of action components clipped at actuator input. Entropy is logged even when its loss coefficient is zero |
| Approximate KL and clipped fraction | Policy change and how often ratios cross the clipping window | Compare against reward, many updates and the actual evaluation. Clipping does not bound every policy change |
| Explained variance | Relative prediction skill for the critic targets | Near 1 suggests close fit, near 0 suggests little advantage over a constant, negative indicates poor fit. Constant targets can make the statistic undefined |
| Raw curves and EMA | Optimizer observations and a smoothed visualization | Read the numeric axis. Signed-log display preserves sign but changes spacing |
| Reward and penalties | Environment reward, individual costs and episode totals | Match step and episode boundaries with contacts and replay. A peak loss and a large negative reward are different measurements |

Start a debugging session with one failed episode. Record whether the
source was visible, where the TCP was commanded, which physical phase
first diverged, which geometry touched first, how far bystanders moved
and whether final verification agreed with the video. Examples of
testable hypotheses follow.

| Observation | Experiment that can disambiguate |
| --- | --- |
| The arm repeatedly closes beside the piece | Freeze the policy, move the piece by a known XY shift and compare camera-derived pickup points and commanded TCP in metric units |
| Lift succeeds in isolation and fails on a full board | Run the same target with zero and multiple neighbors, inspect the first collision pair and distinguish finger approach from wrist/body clearance |
| Reward improves while placement fails | Check which cost decreased, replay terminal frames and compare visual success, toppling and displacement separately |
| The policy acts similarly across images | Pair frames with the same task and commands but change one visible condition. Compare actor means with a zero-residual baseline and a controlled image ablation |
| Training runs slowly | Profile rendering, AC:Vision, physics, logging and PPO separately. Compare headless and watched executions with matched configurations |

### Design the evaluation before training

Separate training, model selection and final test seeds. Vary position,
piece type, occupancy, lighting and camera perturbations according to a
written plan. Compare zero residual, initialized policy and learned policy
under the same seeds. Keep optimization budgets comparable across
ablations. Report successes and trials, uncertainty intervals, contacts,
max displacement, toppling, vision rejection and wall time. Split the
results by scenario. A small successful run on one known transfer is
evidence for that run and setup. Hardware release requires independent
checks on calibration, delay, homing, safety limits and repeatability.
[Deep RL at the Edge of the Statistical Precipice](https://arxiv.org/abs/2108.13264)

## 8. Reconstruction roadmap

Treat each row as a project with an exit test. Skip a row when you can
perform its exit test and explain the assumptions from memory.

| Stage | Study and build | Exit test |
| --- | --- | --- |
| A. Scientific computing | Python, NumPy, tensors, Git, units, determinism and profiling | Recreate a logged result from a clean checkout, config and seed |
| B. Mathematics | Linear algebra, affine/projective maps, chain rule, probability, expectations, Gaussian log likelihoods and KL | Derive a Gaussian mean gradient and verify it numerically |
| C. Mechanics | Frames, rigid transforms, forward/IK, Jacobians, collision, friction, position servos and timing | Draw the transform chain and predict the commanded tool point for known joints |
| D. Vision | Pinhole projection, distortion, ArUco, homography, registration, uncertainty and occlusion | Localize a shifted piece in metric coordinates using only an image and independently measured references |
| E. RL foundations | Bandits, MDP/POMDP, Bellman equations, Monte Carlo, TD, on-policy sampling and discount | Solve a small MDP by hand and reproduce it with code |
| F. Deep learning | Backpropagation, convolution, nonlinearities, initialization and Adam | Build the dashboard network and reproduce all layer shapes and parameter counts |
| G. PPO | REINFORCE, actor-critic, GAE, clipping, bootstrapping and evaluation | Train your own continuous-action PPO on a toy task and explain each loss and stored tensor |
| H. Hybrid manipulation | Task phases, residual control, bounded commands, reward isolation and recovery | Implement camera-to-plan and camera-to-policy, then compare learned residuals against the deterministic planner |
| I. Experimental robotics | Curriculum, ablation, transfer, domain randomization and measurement | Compare pawn and knight variants, crowded boards and capture sequences under held-out conditions. Document which behaviors are still unqualified |

**Capstone.** Start with a blank Python project and one simple board scene.
Use a synthetic image only until the camera-to-board transform passes an
independent metric test. Build a deterministic single-piece transfer, add
an RGB-only actor and simulator-only supervision, and train the smallest
policy that improves a predefined failure mode. Then add a neighboring piece,
compare two residual budgets, and hold back a crowded position until the
final evaluation. Deliver a runnable environment, tests, frozen configs,
metrics with uncertainty and at least one explained failure video.

When designing the next version, write down which signals will exist on
the physical system, what can be inferred from them, what the deterministic
controller already solves and which residual behavior needs learning.
Then choose the experiment that can falsify that design. If the initial
baseline misses the square for a geometric reason, fix or quantify that
error before interpreting a policy update. If viewpoint or friction is
the major error source, randomize it over measured plausible ranges and
test the unchanged hardware-facing interface separately.

## 9. Annotated references

### Core books and courses

- **Sutton and Barto, _Reinforcement Learning: An Introduction_, 2nd ed.**
  Read chapters 2–6 for bandits, MDPs, dynamic programming, Monte Carlo and
  TD. Then read chapter 13 for policy gradients. Implement a small example
  while reading each part. [MIT Press](https://mitpress.mit.edu/9780262039246/reinforcement-learning/)
- **Goodfellow, Bengio and Courville, _Deep Learning_.** Use chapters
  2–4 for algebra, probability and numerical computation, chapters 6 and 8
  for backpropagation and optimization, and chapter 9 for the CNN.
  [Book and chapter index](https://www.deeplearningbook.org/)
- **Lynch and Park, _Modern Robotics_.** Study configurations, rigid
  transformations, kinematics, Jacobians, IK and trajectory generation.
  Re-derive the planar SCARA case while following the general treatment.
  [Author site, preprint and videos](https://modernrobotics.northwestern.edu/)
- **Hartley and Zisserman, _Multiple View Geometry in Computer Vision_.**
  Focus on projective geometry, 2D transformations, camera models and
  estimating geometry from noisy correspondences. [Authors' book site](https://www.robots.ox.ac.uk/~vgg/hzbook/)
- **Tedrake, _Underactuated Robotics_.** Use the notes for dynamical
  systems, feedback, optimization and contact-aware control.
  [MIT course notes](https://underactuated.mit.edu/)

### Papers and implementations by question

| Question | Reading and exercise |
| --- | --- |
| How does a policy improve without a target action label? | Derive the score-function gradient with Sutton and Barto, then compare the ratio, clip and surrogate in [Schulman et al., PPO](https://arxiv.org/abs/1707.06347) and [Spinning Up PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html). |
| How does a late outcome influence earlier actions? | Implement the reverse recursion and compare different `λ` values in [Schulman et al., GAE](https://arxiv.org/abs/1506.02438). |
| Why retain the classical controller? | Compare what each approach learns in [Johannink et al., Residual RL for Robot Control](https://arxiv.org/abs/1812.03201) and [Silver et al., Residual Policy Learning](https://arxiv.org/abs/1812.06298). |
| Why might my PPO differ from the library? | Compare [SB3 PPO](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html), [CleanRL PPO](https://docs.cleanrl.dev/rl-algorithms/ppo/) and [Implementation Matters](https://arxiv.org/abs/2005.12729). |
| What defines a transition boundary in code? | Reproduce terminal and time-limit cases in [Gymnasium's time-limit guide](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/). |
| How does the simulator produce contact feedback? | Derive the role of contact constraints and friction using [Todorov, Erez and Tassa, MuJoCo](https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf) and the [MuJoCo computation manual](https://mujoco.readthedocs.io/en/latest/computation/). |
| Why do fiducials help? | Study marker identity and orientation in [Garrido-Jurado et al.](https://doi.org/10.1016/j.patcog.2014.01.005), then run the [ATOM homography protocol](../../../../docs/camera-rl/homography-experiment-protocol.md). |
| What survives a domain change? | Design a measured visual perturbation study from [Tobin et al., Domain Randomization](https://arxiv.org/abs/1703.06907), then add real calibration and test data. |
| How much evidence is enough? | Use [Agarwal et al., Deep RL at the Edge of the Statistical Precipice](https://arxiv.org/abs/2108.13264) to choose uncertainty summaries and guard against selecting a lucky seed. |

### Repository evidence and decisions

- [P038 pipeline walkthrough](../../../../docs/camera-rl/P038-pipeline-walkthrough.md) and [ArUco installation guide](../../../../docs/camera-rl/aruco-installation-guide.md) cover the implementation history and marker setup.
- [S018 camera and board-state localization](../../adrs/S018-board-state-camera-localization.md), [S019 intermediate policy transfer](../../adrs/S019-intermediate-policy-transfer.md) and [S020 dashboard telemetry](../../adrs/S020-ppo-dashboard-telemetry.md) record the current decisions.
- [Broader reinforcement learning roadmap](../../../../docs/reinforcement-learning/README.md) expands the math and research track and marks earlier workflows as historical.
