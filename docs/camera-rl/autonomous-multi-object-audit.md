# Autonomous multi-object manipulation audit and implementation plan

Audited on 2026-11-07 against branch `ros2_simulation`, HEAD `08f5f77`, including
the existing uncommitted autonomous prototype. Local changes and historical
artifacts form part of the evidence. They are preserved. This is the Milestone 1
record for the Autonomous Manipulation Learning Platform request.

## Measured starting point

The native-viewer pilot `302c79a87cc84ae09b034ebfe20c8c7f` collected 128
decisions, of which 106 passed supervision, 18 failed IK/limits and four
failed swept collision checking. Four training episodes and three held-out
evaluation episodes had zero reach success. No bilateral grip or lift was
recorded. `ACCEPTED` describes an executable nominal segment.

The matching three-panel pilot `e455937e846a40858d71092802810d00` has the same
validation counts and zero evaluation success. The interrupted lift pilot
`4969538bba834b929b9d9c0295513bf8` recorded 92 decisions before
`RESET_PERCEPTION_FAILED`, with 74 accepted and zero bilateral grips/lifts.
Source records are under `simulation/mujoco/training/autonomous-manipulation/runs`.

The archived residual experiment `pawn-e2-e4-camera-25f687b84c474ffc81e54eec6af40dcc`
added 4,096 decisions to transferred weights. Its report records zero success
for both its paired baseline and residual evaluation. The finite approach
investigation screened 2,600 and 312 candidates with zero accepted approaches.
Those samples do not establish impossibility outside that family.
[Investigation and links to reports](approach-strategy-study.md)

## Component inventory

| Component | Existing implementation | Reuse and limitations |
| --- | --- | --- |
| Chess Core | `Software/acchess`, integration `chess_move_request`, engine turn planner | Legal chess/task context, UCI integration. Manipulation training uses explicit fixture FEN. Live engine-to-learned-policy qualification is pending. |
| AC:Vision | Native C ABI in `Software/acvision/runtime`, `native_vision.py` | Real RGB processing, ArUco orientation, homography and rectification. Square candidates and silhouette registration provide occupancy/planar evidence. No measured six-kind recognition during a grasp or 3D grip tracking. |
| Motion | `Software/acmotion`, `native_motion.py` | Native IK and planning, bounded wrist adapter, FK consistency checks. Autonomous actions use IK and supervision. Residual actions follow nominal waypoints. |
| Physical state | `physical_state.py`, `task_plan.py`, Chess task adapter | Separate logical and physical occupancy, captures and graveyard task representation. A new policy still needs verified transport/release and reconciliation integration. |
| Simulation | `backend.py`, model builder, interactive model | MuJoCo gravity, free pieces, board and graveyards, six actuator targets including coupled fingers and bounded wrist. Experimental physical properties. |
| Safety | `collision.py`, `autonomous_control.py`, contact supervision | Conservative nominal sweeps with explicit exclusions, rigid carried-object approximation, dynamic contact/topple checks. This is model-scoped evidence. General hardware safety and recovery require calibrated observed geometry. |
| Legacy learning | `simulation/learning`, `training/grasp-lift` | Kinematic SAC and pixel PPO experiments, optional multiple CPU workers/arena. Their observations, controls and checkpoints differ from autonomous manipulation. |
| Residual learning | `training/camera-manipulation` | CNN plus task/command vectors and PPO, paired baseline/evaluation, CSV and dashboard. Nominal approach, grasp and transport geometry constrains exploration. |
| Autonomous learning | `autonomous_env.py`, `training/autonomous-manipulation` | Seven temporal controls for XYZ, wrist, fingers, elbow and duration. Version 2 had no object conditioning and inherited residual reset/calibration work. Version 3 changes are tracked in S025. |
| Dashboard | `training/camera-manipulation/dashboard*.py` | Real network hooks, losses, rewards and progress. The autonomous launcher initially never connected the publisher. S024 specifies that integration. |
| Firmware | `firmware/esp32-s3-motion` | ACM1 parsing, J1/J2/J3/Z/servo targets, cancellation and safety defaults. `configured=false` requires measured hardware configuration. No simulator result validates these actuators. |
| ROS/Gazebo | `simulation/src`, module guides | Separate diagnostic and simulation path. Historical RViz frames and profiles do not certify current MuJoCo geometry. |

## Objects and geometry

The loaded full-board pawn fixture contains 32 separate free bodies and all
six geometric kinds in both colors. There are eight pawns, two knights, two
bishops, two rooks, one queen and one king per color. Color reuses geometry.

| Kind | Exported source visual | Active piece collision proxies | Qualification state |
| --- | --- | --- | --- |
| Pawn | `pawn.stl` | Cylinder base/stem, sphere head | Most historical learning evidence. No qualified autonomous grip/lift. |
| Knight | `knight.obj`, original STL retained | Cylinder base/stem, box head | Earlier isolated/starting-position residual fixtures exist. Existing knight evaluations inspected had zero approval. |
| Bishop | `bishop.stl` | Cylinder base/stem, sphere head | Visual asset available, autonomous manipulation qualification pending. |
| Rook | `rook.stl` | Cylinder base/stem, box head | Visual asset available, autonomous manipulation qualification pending. |
| Queen | `queen.stl` | Cylinder base/stem, sphere head | Visual asset available, autonomous manipulation qualification pending. |
| King | `king.stl` | Cylinder base/stem, two cross boxes | Old inherited reset requests a nonexistent `_head` geom. Dedicated autonomous scene avoids this assumption. |

The source is `hardware/Project/chess_pieces/ChessPieces.3mf`, accompanied by
the Blender file and exported hash manifest. The builder generates visual
LOD meshes on a 0.3 mm grid. Source mesh dimensions are documented in the
manifest. Visual surfaces and collision surfaces differ.

The audited bundle has 311 geoms, 42 bodies and 230 generalized positions.
Its full-gripper profile includes 66 experimental decomposition hulls plus
fingertip pads. Piece bodies use an assigned mass of 0.02 kg and diagonal
inertia `[0.000004, 0.000004, 0.000002]` kg m². Contact friction and controller
gains are experimental assignments, without measured material/force data.
The fingers use coupled slides with travel −0.021 to 0 m. The wrist spans
0 to 2π rad, with switch calibration pending. Its fitted assembly pivot is
documented in S010. The real servo linkage is not reconstructed.

The model uses 35 mm squares and experimental graveyard supports. Hardware
board files include G-code, with assembly reconstruction still a separate
geometry task. CAD mesh availability does not validate physical collision
accuracy, mass, friction, force limits or real grasp points.

## Camera and policy boundary

Shared camera settings live in `virtual_camera.py`, with optional explicit
per-experiment overrides. The audited full-board fixture uses distance
1.05 m, azimuth 180°, elevation −75°, 1920×1440 RGB and look-at
`[0.245, 0, 0.012]`. ArUco layout is a versioned bundle asset. The H-file
marker installation guide documents its experimental physical mapping.

Version 2 receives two rectified 96×96 RGB frames, task endpoints, command
history, previous actions, perception validity and objective. It receives no
live MuJoCo poses or contacts. The simulator supervises reward and safety.
Source offset registration is RGB-derived but was not explicitly available
as a compact actor feature. Fixed board-to-robot calibration still comes
from the experimental fixture and requires real-world calibration.

Version 3 adds expected logical kind/color and camera-estimated planar
source context relative to commanded FK. Stale/occluded visual estimates
must carry validity/age. Whole-object 3D tracking and hardware perception
remain open. The explicit isolation test must keep actor inputs identical
when hidden physics changes with fixed images and host commands.

## Learning, reward and performance diagnosis

The first prototype uses SB3 PPO MultiInputPolicy. A NatureCNN encodes six
stacked image channels, its features are fused with task/host vectors and
separate actor/critic MLPs. Gaussian action sampling provides exploration.
The seven controls integrate over a selected number of control intervals.
There are no learned hierarchical options. Discounting is per decision
despite varying physical duration.

The old reward uses change in mean nonnegative pad-to-piece distance divided
by collision-model piece height, a −0.01 time cost, −0.001 times action squared
norm, rejection costs of −1 through −6, one-time grasp +2, lift +3, success
+10, timeout −5, failure −5, contact −20, displacement −1 per additional mm
beyond its settling dead band, and toppling −50. Config values can differ.
The old proximity calculation also included the visual mesh. S025 aligns
it with active physical colliders. The old reach threshold was 1.5 mm.
Neither the positive contact event nor total return alone proves a stable lift.

The autonomous supervisor currently ends episodes after unexpected contact
or neighbor excursion beyond 0.25 mm. This is stricter than the earlier
requested contact-only penalty behavior and needs an explicit subsequent
training safety contract. Toppling remains a stop condition.

The read-only profile `profile-3e50e5b98b2646d6a8b9893199e24e8d` measured
1.608 s reset and 1.872 s for eight decisions without Watch, about 4.27
decisions/s. Six sweeps consumed 1.017 s, including 2,552 interval samples
and 203,032 distance calls. Native processing took about 29–32 ms per
1920×1440 decision image. Reset included 17 unused appearance observations.
These measurements identify CPU sweep and reset work as first targets.

## CUDA diagnosis

Detected PyTorch `2.14.1+cu130`, CUDA runtime 13.0, SB3 2.9.2, MuJoCo 3.17.0,
RTX 5070 Ti with 16,303 MiB reported by `nvidia-smi`, driver 617.14.
The previous CUDA smoke changed policy weights and verified save/reload.
Actual per-layer devices, gradient/optimizer tensors, synchronized timing,
VRAM and matched CPU/CUDA workload performance still need dedicated capture.
A single idle utilization sample does not measure training acceleration.
MuJoCo physics, native perception and collision checks run on CPU in this
pipeline. Rendering uses OpenGL separately from the PPO compute device.

## Checkpoints and datasets

The recursive inventory found 17 `policy.zip` archives and 97 intermediate
checkpoints under grasp-lift, 27 and 81 under camera-manipulation, and four
and two under autonomous-manipulation. Counts include nested historical
fixtures and partial runs. Some folders contain only reports or failed runs.

| Archive | SHA-256 |
| --- | --- |
| Residual `ed0bde845a754581b62cd664e7b7c7ae/checkpoint-2560.zip` | `1fb245ada29e321814080e4dba7cf7517bae43ceaf9ebb66e02c0e35e9f915ab` |
| Residual `pawn-e2-e4-camera-25f687b84c474ffc81e54eec6af40dcc/policy.zip` | `590310756f7cc71694d36bb5af91dedebde7d8b2c9712c1a90339bd514a23b3c` |
| Autonomous v2 `302c79a87cc84ae09b034ebfe20c8c7f/policy.zip` | `9a65e9ba51324e627392b4dae3e71b54f29a42c0a2704f3cf38e50209eec04b7` |

SB3 archives include policy and optimizer state. Autonomous warm start
explicitly copies weights into a fresh optimizer. It does not restore RNG,
environment state, partial rollout or schedules. Residual resume has its
own integrity checks. Schema-changing policies cannot be transferred merely
because a filename contains a larger timestep number.

`Software/acvision/tests/dataset` contains 57 JPGs and FEN labels. The camera
documentation retains static homography/marker experiments and image reports.
These are perception evidence, not a validated multi-object manipulation
training/validation/test dataset. The new experiments need explicit seed,
object, configuration and scene splits with per-object evaluation histories.

## Proposed architecture and implementation gates

Use one object-conditioned visual encoder/policy with logical task context,
temporal observations, calibrated command estimates and a separate supervisor.
Begin with PPO to isolate environment changes. Compare recurrent PPO for
memory only after measuring an observability limitation. Compare SAC for
sample reuse on the same frozen task. On-policy PPO does not reuse arbitrary
old replay samples. Sequential weight transfer and balanced current-task
sampling are the first shared-policy baseline. Independent specialists are
comparison groups, with forgetting measured on every previous object.

| Milestone | Implementation increment and acceptance |
| --- | --- |
| 1 | This component/object/evidence audit and plan. Report before expensive training or destructive reconstruction. |
| 2 | Real CUDA model diagnostic, matched benchmark, unique experiment records, CSV events, verified checkpoint recovery and bounded smoke. Finite loss/gradient and actual optimizer changes are mandatory. |
| 3 | Dedicated autonomous reset, normalized camera/task context, bounded continuous exploration, explicit reach curriculum and reward diagnostics. Pass hidden-state isolation, rejection immobility, action effects and held-out approach improvement. |
| 4 | Short experiments for each geometric kind/color, separate approach/grip/hold/lift evidence, safe failure classes. Fix model/observation blockers before claiming support. |
| 5 | Balanced combined sampling and one shared policy. Report per-object held-out rates against solo and specialist baselines, including forgetting. |
| 6 | Real event dashboard, visual Watch, hardware telemetry, experiment comparison and backend controls. Pause/resume/stop need tested process state and checkpoint boundaries. |
| 7 | Longer training after preceding stage gates, with periodic evaluation, bounded regression handling and fresh historical outputs. Transport/placement/capture require their own success/reconciliation contracts. |

S023 defines the shared architecture. S024 covers telemetry and checkpoint
evidence. S025 covers the immediate reach experiment. Successful reduced-scene
reach permits longer training of that named stage. It does not qualify the
full-board gripper, stable lift, captures or real hardware. Record every
negative result beside successful checks before advancing.

## Research direction

The primary hypothesis is that a shared conditioned policy can acquire and
retain manipulation across piece geometries through progressive experience.
Balanced sample counts, held-out seeds, separate stages and preserved failures
make this testable. Fixed synthetic geometry, imperfect camera calibration,
scene leakage through initialization, changed reward thresholds and small
evaluation samples are threats that must be reported.

PPO provides the initial on-policy baseline. SAC supplies a later off-policy
sample-efficiency comparison. Temporal options require learning their policies
and termination rules beyond merely holding an action for several frames.
Task balancing and reward scale deserve explicit comparisons in shared learning.
[PPO](https://arxiv.org/abs/1707.06347),
[SAC](https://arxiv.org/abs/1812.05905),
[Option-Critic](https://arxiv.org/abs/1609.05140),
[Multi-task PopArt](https://arxiv.org/abs/1809.04474).
