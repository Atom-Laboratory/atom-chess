# Autonomous Learning of Vision-Guided Robotic Manipulation Strategies Through Reinforcement Learning

Comparison between residual reinforcement learning and hierarchical action selection.

## Revised scope

The next study expands beyond selecting a preset approach. The actor should
discover continuous approach, grasp-height, wrist and elbow decisions from
visual observations and host history. A finite rejected family is retained
as negative evidence. The new prototype uses persistent temporal actions
without a manipulation waypoint sequence. The research hypothesis remains
unverified. [S022 decision](../../simulation/docs/adrs/S022-autonomous-temporal-actions.md)

PPO is the first controlled comparison because the residual experiment
already uses it. Its on-policy samples make a short interface test simple
to audit. SAC is a strong subsequent candidate when replay reuse matters,
at the cost of image replay memory and additional algorithm changes.
Recurrent PPO is a candidate when short image history cannot resolve
occlusion and motion. These are proposed comparisons.
[PPO](https://arxiv.org/abs/1707.06347) ·
[SAC](https://arxiv.org/abs/1812.05905) ·
[Recurrent PPO implementation](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_recurrent.html)

The prototype learns velocity, orientation, finger motion, elbow branch and
duration. The duration controls persistence over several physics intervals.
This is a temporal control primitive. Learned high-level options and
learned option termination require their own later experiment.

## Audit

The reference run is `pawn-e2-e4-camera-25f687b84c474ffc81e54eec6af40dcc`.
It added 4,096 steps to weights transferred from the 2,560-step checkpoint.
Its 38 complete training episodes produced zero approvals. The single paired
evaluation recorded 23 contact intervals for both groups and E1 king excursions
of 12.49 mm (baseline) and 14.71 mm (residual). E4 appearance IoU was 0.622
and 0.595 respectively, below 0.65. These results concern one fixed scene.

| Stage | Current implementation and boundary |
| --- | --- |
| Logical state and RGB | [Chess task adapter](../../simulation/mujoco/src/atom_mujoco/chess_commands.py), [native vision](../../simulation/mujoco/src/atom_mujoco/native_vision.py), [RGB localization](../../simulation/mujoco/src/atom_mujoco/board_piece_localization.py). FEN and fixture identify expected occupants. ArUco rectification and appearance registration estimate planar offsets. The full-board mode uses isolated scratch calibration images. The legacy branch constructs an empty-source reference from a copy of live qpos and must stay outside the new policy path. |
| Actor observation | [Observation builder](../../simulation/mujoco/src/atom_mujoco/camera_policy.py), [Gym contract](../../simulation/mujoco/src/atom_mujoco/camera_manipulation_env.py). Dict of rectified RGB CHW 3×96×96, source/destination coordinates, last action, commanded joints, phase index, and perception-valid flag. Commands are estimates of what the host sent. True joints, contacts, and body poses are absent from this payload. Neighbor XY estimates are recorded in info and remain outside the actor observation. |
| Action | [CameraOnlyEnv](../../simulation/mujoco/src/atom_mujoco/camera_only_env.py). Five normalized continuous components in the wrist fixture. Bounds for this run are ±2 mm in X and Y, ±2.25 mm in Z, ±1 mm in coupled finger slide command, and ±0.2 rad at the wrist. Cartesian and opening residuals apply at each step. With visual qualification the wrist residual is sampled once at phase 0 and once at phase 4, then held through descent. It slews at up to 1 rad/s around nominal 72° pickup and 164° transport orientations. |
| Planner and execution | [Native Motion adapter](../../simulation/mujoco/src/atom_mujoco/native_motion.py) asks AC:Motion for eight waypoints and IK. The residual modifies each waypoint before IK. The low-level controller rate-limits commands and steps physics. Phase advance uses command convergence and dwell, which provide no evidence of physical grip. The residual loop does not sweep-check each action path. |
| Reward and success | [CameraOnlyEnv](../../simulation/mujoco/src/atom_mujoco/camera_only_env.py) and [contact supervision](../../simulation/mujoco/src/atom_mujoco/contact_supervision.py). Time and action costs, configurable costs for any forbidden contact in a control step and new peak bystander excursion beyond a 0.25 mm dead band, toppling termination, and a final visual bonus. Destination occupancy, upright appearance and neighbor image consistency are required. Grasp and lift are unverified in this path. |
| Evaluation | [P038 launcher](../../simulation/mujoco/training/camera-manipulation/run.py) pairs zero residual with deterministic policy inference on the same seeds. The reference run used one seed and trained stochastically. A fixed camera, occlusion, one occupancy configuration, and a lack of separated grasp/lift verification limit interpretation. |

Reuse native vision, board localization, task identity, the AC:Motion IK,
swept geometry checker and position controller. A future selection policy
needs a persistent approach choice, validated execution, separated physical
and RGB evidence and an explicit recovery contract. Keep the residual runner
and its checkpoints as comparison groups.

## Research question and hypotheses

Does choosing a physically distinct approach from RGB and task context
improve manipulation among neighboring pieces compared with bounded residual
control on fixed waypoints? Our unverified primary hypothesis predicts higher
paired approval under the same physical fixture. Secondary hypotheses concern
diverse angle and approach families, consistency during descent, the benefit
of visible neighbor context, recovery after a rejected attempt, and the
possible divergence between return and physical approval.

## Protocol and decision gates

1. Screen geometries on the existing E2/E1 full-board fixture. Derive trial
   offsets from the existing residual bounds, stem and approach geometry.
   Sweep wrist travel within model limits. Hold the camera, collision
   geometry, controller and physics constant. Distinguish IK rejection,
   sampled clearance rejection, conservative swept rejection, and executed
   pickup failure. Save every candidate and rejection reason.
2. Run only sweep-accepted paths in live simulated dynamics. Use independent
   bilateral pad contact, raised piece height, stable hold and bystander
   excursion checks. Keep RGB evidence separate. Arm settling and contact
   do not imply visual confirmation. Stop after an unsafe state instead of
   trying an unqualified physical recovery.
3. Require multiple physically distinct, repeatable approaches before a
   learned selection comparison. One successful pick-and-lift is feasibility
   evidence only. Recovery needs a separately checked reverse path, an
   observed unchanged scene and refreshed perception. Uncertain physical
   state requires reconciliation. A preflight rejection before motion can
   allow another choice without a retreat.
4. Once gated, compare zero residual, the archived 2,560 and 4,096-step
   checkpoints, a strategy policy, and a strategy-plus-recovery variant if
   implemented. Pair identical seeds and calibrated fixtures. For a fair
   study, compare all groups on the same task endpoints and criteria. Report
   pickup-only and full-transfer outcomes separately. Keep training seeds
   separate from evaluation seeds. Freeze geometry, rewards and acceptance
   checks for final evaluation. Record training/inference sampling mode.
5. Gate transport, then release/placement, then varied piece and neighbor
   configurations. Measure pilot variance before committing to a sample
   size. Report counts and uncertainty, including paired failures. The
   search budget is exploratory and does not estimate statistical
   significance or prove infeasibility outside the sampled families.

## Metrics

Independent variables include policy class, persistent wrist, approach XY,
pickup XY, approach height, descent path, aperture, recovery mode, fixture,
seed and optimizer settings. Record grip as simultaneous selected-piece
contact at both finger pads, lift as vertical rise beyond the configured
geometric threshold, and stable hold as uninterrupted qualifying evidence
over the dwell window. Record collision pairs and affected intervals,
maximum bystander excursion from the settled start in millimeters,
toppling, and sampled or conservatively verified clearance with its scope.

For later stages, transport succeeds when a verified hold reaches the
destination approach without disallowed contact. Placement requires verified
release and stable correct occupancy. Whole-task approval requires all
applicable gates. Log recovery attempts and successful validated retreats
separately. Track per-component return, wall and simulated duration,
destination IoU, visual confirmation and invalid perception counts. Keep
physical and visual rates separate.

Save date, source and config hashes, code revision, fixture identity, seeds,
candidate parameters, checkpoint digest where applicable, output records
and limitations in a fresh directory. The current experiment is simulated.
Geometry, friction and visibility require physical qualification before
hardware use. A single scene or seed cannot demonstrate generalization.

## Experiment 1 results

The full-board fixture, camera, native binaries, model, and contact geometry
match the reported E2 → E4 experiment. The search uses AC:Motion for IK and
the RGB-derived source and bystander XY offsets for its nominal scene.
Ground-truth body state is reserved for potential dynamic trials. Both
residual checkpoints remain available in their original run directories.

| Run | Seed | Endpoint candidates | Endpoint rejections | Swept checks | Dynamic trials |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Main grid](../../simulation/mujoco/training/camera-manipulation/runs/approach-matched-contact-38973b6700c440c5bb7402f8a8718c57/report.json) | 100007 | 2,600 | 2,600 | 0 | 0 |
| [Replication subset](../../simulation/mujoco/training/camera-manipulation/runs/approach-second-seed-a8a5bdda285744ceb84ddb5d135f2f47/report.json) | 100008 | 312 | 312 | 0 | 0 |
| [Centered angle diagnostic](../../simulation/mujoco/training/camera-manipulation/runs/approach-diagnostic-e512e6f18516431896a48227a0868571/report.json) | 100007 | 26 | 13 against the king | 3, all rejected | 0 |

The main grid crossed 26 wrist angles, including the reference 72° angle,
with five entry points (center and 8 mm in each cardinal direction), five
grasp points (center and 2 mm in each cardinal direction), two approach
heights (nominal and +2.25 mm), and two aperture settings (nominal and 1 mm
less finger-slide opening). The wrist grid covers the bounded 0–360°
revolution. Offsets use the existing model and residual limits as scales.
The offset entry yields an oblique final leg. Pickup Z and the intermediate
descent height were held fixed. The subset includes centered and one-factor
changes, plus a small portion of combined changes.

Every main-grid candidate was rejected at the low descent endpoint. Of
the recorded first blocking pairs, 2,300 had negative signed distance and
300 were below the 1 mm nominal sweep margin without recorded penetration.
The king accounted for 1,116 first rejections, the D2 pawn for 624 and the
F2 pawn for 434. Other blockers included the bishop, queen and non-pad
geometry against the selected pawn. Pad-to-target contact was allowed
during descent and closure. The counts report the first blocking pair
in checker order and cannot be read as independent collision probabilities.

| Centered wrist | Main grid first blocking pair | Signed distance |
| --- | --- | ---: |
| 72° | Hand hull and E1 king stem | −11.51 mm |
| 0° | Hand hull and D2 pawn stem | −1.55 mm |
| 180° | Hand hull and F2 pawn stem | −1.55 mm |

[MuJoCo comparison render](../../simulation/mujoco/training/camera-manipulation/runs/approach-matched-contact-38973b6700c440c5bb7402f8a8718c57/blocked-descent-comparison.png).
The panels reconstruct each rejected descent waypoint from its recorded
joint command and the RGB-derived scene offsets. The inspection camera and
colors are diagnostic. Red identifies the tested convex hand hull, and
yellow identifies the blocking piece proxy. These are static model poses.
The fixture square pitch is 35 mm. Both illustrated hand hulls belong to
`gripper_hand1_moving` and are active mesh colliders in the recorded model.

The centered angle diagnostic screened the king only and then used the full
continuous checker on its three highest-clearance candidates. At 0° and
180°, the conservative checker found interference with the D2 and F2 pawn
heads respectively (about 3.17 mm penetration at sampled swept
configurations). The third path exhausted the sweep budget on approach.
A king-only check would therefore admit options that fail against adjacent
pawns. The initial all-geometry screening pilot also rejected early
pad-to-target proximity. Its protocol was superseded by the main grid,
which matches the established pad-contact exemption. All artifacts were
preserved. Each run directory includes its protocol, exact input
configuration, source hash, revision, seed, and candidate parameters.

There is no measured grip, lift or visual verification rate for this
search, because no candidate was admitted to dynamic execution. The
measurements point to the volume occupied by the gripper hull during the
descent, under the current model and path family. They do not prove that
the hardware collides or that all feasible trajectories have been exhausted.

## Conditional design for the next increment

After the feasibility gate, expose immutable strategy identifiers or bounded
approach parameters to an approach policy. Bind one selection to a single
attempt and pass it through native IK and a sweep over a camera-derived
scene. Persist the actual validated waypoints through descent. Make a fresh
preflight decision when the perception frame becomes stale or the scene
changes before motion. Keep the actor payload to RGB, observed piece
geometry, logical context and command history.

Classify preflight rejection, lost perception, unintended contact, failed
closure, unverified lift, displaced pieces, toppling and unknown physical
state separately. Retry after a preflight rejection from the unchanged park
pose. A physical retry requires an independently validated retreat and a
reconciled scene. The first training curriculum should distinguish
bilateral grip, lift and stable hold with separate supervision and separate
visual evidence. Costs should remain visible per component. Avoid rewarding
an idle approach or treating a command as physical feedback.

The next geometry investigation should compare the specific hand hulls
against their CAD source, verify wrist/TCP and aperture alignment, and test
additional grasp heights and IK branches with explicit scene provenance.
The P038 residual policy, strategy selector training and physical recovery
are separate increments. The selector and recovery gate remain closed until
validated alternative approaches exist.

## Autonomous temporal control pilot

The newer environment explores continuous TCP, wrist and finger motion,
elbow branch and duration. The actor receives two RGB frames and host
commands. IK and velocity checks run before a swept collision gate.
The environment retains the full E2/E1 board and monitors simulated
contacts and displacement independently of the actor.

| Pilot | Objective | Training decisions | Admitted segments | Deterministic evaluation |
| --- | --- | ---: | ---: | --- |
| First autonomous interface | Lift | 32 | 0 | 0 of 2 |
| Shorter kinematically feasible increments | Reach | 128 | 111 | 0 of 3, all time limits |

The second run used seed 7, a 32-decision horizon and evaluation seeds
910000 through 910002. It produced 638 recorded TCP samples from executed
control intervals, 98 accepted spatial/orientation bins, 13 IK or joint
limit rejections and four speed rejections. None of its logged training
decisions recorded a forbidden bystander contact. The actor requested
the alternative elbow branch 11 times. All admitted commands used the
down branch. The policy archive hash is
`29e79d758ee1a9d5a8d879b5f42f0d1c15d078f98f181e496453059d15b6ca91`.
The run directory is `reach-optimized-watch-0d16321f8c46417abddda9992b73e89b`.
The run report records the hashes and the decision log records requested
commands, validation and measured motion.

The two pilots used different budgets and objectives. Their counts show
that exploration can now execute physically distinct motion segments.
They do not estimate comparative learning performance. No evaluated
episode met the reach objective, and this pilot did not test qualified
grasp, lift, transport or placement. The archived residual runs used a
full-transfer criterion and remain separate comparison groups until
all policies can be tested on the same task and seeds.

The subsequent performance check replayed four identical actions twice
per implementation at seed 100007. The earlier sweep took 6.31–6.34 s.
Reusing parent clearance certificates and updating only kinematics took
1.28–1.30 s for the same decisions. Verdicts, sample counts and executed
TCP traces matched exactly on that replay. A separate 32-decision smoke
run completed with the native Watch and CUDA on an RTX 5070 Ti. These
measurements describe execution throughput for the tested actions.
