# Hybrid planning and local RL — M1 repository audit

Date 2026-11-07. Source branch `ros2_simulation`, HEAD
`1997dd60bdb1738afb3cccba973d64087b7117ef`. This audit inspects the current
implementation and executes existing regression tests. It creates documentation
and evidence only. Implementation, planner changes and training remain gated
on reporting M1 as required by the new hybrid roadmap.

The pre-existing untracked `simulation/mujoco/examples/train_visual_grasp.py`
is preserved. Historical runs and checkpoints are preserved. No commit or push
belongs to this increment.

## 1. Diagnosis

There are reusable native vision, task planning, IK, simulation, collision,
feedback and learning components. They currently form several execution
paths with different capabilities. A complete six-command hybrid path with
explicit planner/local-policy ownership has not been implemented.

| Priority | Verified finding | Consequence for the next milestone |
| --- | --- | --- |
| P1 | `MotionPlanner::planTask` expands a transfer into eight fixed Cartesian waypoints. It has no obstacle-scene input or route search. | Treat it as a trajectory proposal generator and qualify complete approach paths with the existing collision layer. |
| P1 | Automatic `Playground` rejects bundles containing `wrist_joint`. The P015 trajectory reader accepts only five named commands. | Wrist-capable training cannot be assumed to run through the automatic chess/trajectory execution interfaces. |
| P1 | The deterministic capture regression loses grip during transport. Isolated reproduction also fails. | A deterministic capture/transport baseline is currently unqualified. |
| P1 | The 2,600- and 312-candidate searches reject every candidate at a descent endpoint. No candidate reaches their swept or dynamic stages. | Those records identify endpoint obstacles and do not establish excessive sweep conservatism or global infeasibility. |
| P1 | Autonomous randomized starts initialize the robot directly at admitted poses. | Local admission does not demonstrate a path from park or a planner-to-policy handoff. |
| P1 | Piece collision proxies and visual source mesh dimensions differ substantially. Gripper linkage, masses and friction are experimental. | Establish model provenance and collision scope before attributing failures to the real CAD assembly. |
| P1 | The normalized pilot stopped with a joint-limit exception and has no final trained evaluation. | Its saved weights and numerical tests provide infrastructure evidence, without qualifying a learned grasp/lift. |
| P2 | There is no enforced local-workspace envelope or planner/RL ownership state in the autonomous environment. | Small bounded increments can accumulate into global motion. M3/M4 must authorize local execution explicitly. |
| P2 | Camera reference validity and target-object visibility have different checks. A remembered source can remain in use while the target is occluded. | Define confidence, freshness and reconciliation behavior before visual handoff. |
| P2 | Simulator grip/lift feedback has no implemented camera-only hardware equivalent. | Visual verification is an open gate, including the return to planned transport. |

## 2. Existing motion architecture

The C++ [MotionPlanner](../../Software/acmotion/src/motion_planner.cpp)
generates source approach, lowering, closure, lift, destination travel,
lowering, opening and retract poses. Safe and pick heights are constructor
parameters. `planTask` accepts `MoveBoardPiece` and `RemoveCapturedPiece`.
Physical promotion is explicitly unsupported. Default HOME/staging coordinates
are predefined values requiring qualification for the selected robot.

[TaskPlanner](../../Software/acmotion/src/task_planner.cpp) expands chess moves
into physical tasks, including captured-piece removal. Chess legality belongs
to `acchess`. [The integration CLI](../../Software/integration/src/chess_move_request.cpp)
validates move history and exports square-based steps. Its internal example
mapper uses a provisional grid. The CLI output contains symbolic endpoints,
which the Python adapter resolves against its physical scene. Those internal
example coordinates are not hardware calibration.

The analytic [InverseKinematics](../../Software/acmotion/src/inverse_kinematics.cpp)
solves a selected planar two-link branch, auxiliary J3 orientation, Z and
gripper target. It checks finite inputs, radial reach and configured joint
limits. It has no obstacle-aware search. The selected branch is configurable,
with explicit Python support for up/down choices in the autonomous path.

[MotionExecution](../../Software/acmotion/include/motion/motion_execution.hpp)
provides protocol execution states, sequence checks, acknowledgments, timeouts,
cancellation and controller faults. Successful DONE handling does not establish
measured joint position, grip or board occupancy.

## 3. Native interfaces and trajectory/execution paths

The motion ABI is version 1, implemented in
[motion_runtime.cpp](../../Software/acmotion/runtime/motion_runtime.cpp).
`acmotion_plan` receives world XY and heights in millimeters and returns
eight rows of XYZ/gripper percentage. It calls the existing C++ `planTask`.
`acmotion_solve` receives a 14-double geometry vector, a Cartesian/gripper
target and an elbow selector. It returns five simulated command components.
Errors are exposed through `acmotion_error`.

[NativeMotion](../../simulation/mujoco/src/atom_mujoco/native_motion.py)
derives geometry and limits from the selected static model, converts SI/world
coordinates to the C++ ABI and checks FK agreement on sample configurations.
When a bounded wrist is present, it recomputes the effective tool offset/link
geometry for the requested wrist and appends that wrist target to the five
returned components. The C ABI does not export per-waypoint wrist orientation
or a collision-certified approach-region contract.

| Execution path | Generation and supervision | Current scope |
| --- | --- | --- |
| Automatic Playground | Python numerical `Playground.solve`, preshape/grasp waypoints, `SceneCollision.check_plan`, controller and oracle feedback | Square/physical tasks and state reconciliation in a five-command profile. Constructor rejects wrist bundles. |
| P015 C++ trajectory | Exported joint JSON, strict profile/joint-order validation and execution | Fixed five-command schema. A six-command wrist trajectory is rejected. |
| Physical-reward P038 | C++ eight-waypoint plan and native IK with per-step supervision in the base environment | Scripted manipulation phases with local residual actions and simulator task feedback. |
| CameraOnlyEnv | C++ nominal plan, RGB-localized source, residual commands, RGB task checks and optional simulator contact/displacement penalties | Has wrist controls, but its overridden step does not call the base `_supervise` sweep method. Contact supervision alone is not complete swept validation. |
| Autonomous environment | Camera/task features, accumulated temporal commands, native IK, independent sweep and dynamic checks | Supports the wrist, without calling `planTask` for global approach or returning ownership to a planner. |

The [P015 reader](../../simulation/mujoco/src/atom_mujoco/trajectory_execution.py)
hardcodes five joint names and a position-only profile. The
[Playground constructor](../../simulation/mujoco/src/atom_mujoco/playground.py)
explicitly raises on `wrist_joint`. These constraints are verified from code,
even though the RL path now includes wrist actuation.

## 4. Current collision implementation and model evidence

[SweptChecker](../../simulation/mujoco/src/atom_mujoco/collision.py) recursively
checks nominal joint-linear intervals using geometry distance queries and
conservative motion bounds. Default clearance is 1 mm, maximum depth is 16,
and an interval call fails closed at its sample budget of 4,096. The opt-in
sphere pruning path retains unbounded geometry and unresolved-pair checking.
These are existing experimental checker settings, not measured physical
tolerances.

`SceneCollision` forms robot/environment, selected-piece/environment and
non-excluded robot-pair checks. Structural welded/adjacent pairs have explicit
exclusions. Selected-piece pad contact and resting support have phase-specific
allowances. Transport uses an approximate rigid carried-piece pose and
additional motion bounds. Dynamic feedback still matters because actual
contact dynamics can depart from a nominal sweep.

The audited bundle has six command entries and 32 free piece bodies. Its
manifest describes 66 full-gripper decomposition hulls plus fingertip pads.
The physical simulator profile marks robot self-contact simulation disabled,
while the explicit checker separately includes non-excluded robot pairs.
This distinction must remain visible when reporting collision coverage.

Static inspection reproduced these source visual and primitive proxy heights.

| Kind | Visual source height (mm) | Physical proxy height (mm) |
| --- | ---: | ---: |
| Pawn | 34.6348 | 32.00 |
| Rook | 43.0898 | 36.00 |
| Knight | 54.4412 | 46.18 |
| Bishop | 56.8397 | 44.00 |
| Queen | 62.7168 | 48.00 |
| King | 71.2265 | 56.00 |

All six source visual kinds exist in both colors. Every audited piece body
has an assigned 0.02 kg mass. Mass/inertia/friction, gripper forces and rail
coupling remain synthetic. The finger slides span −0.021 through 0 m with
equality coupling. The wrist spans 0 through 2π rad. Its switch sign/zero,
physical speed and servo linkage require hardware calibration. Source hashes,
the geometry vector, camera, joints and profile are retained in the
[inspection record](evidence-hybrid-m1/inspection.json).

The approach search's first main-grid rejection is a modeled descent overlap
of about 1.547 mm between `collision_gripper_hand1_1_collision_hull` and
`white_pawn_d2_stem`. Its reported `clearance_m` of about +17.82 mm measures
the sampled king distance, not global clearance. The four most frequent first
reported pairs include the D2 pawn, F2 pawn and E1 king. Pair order affects
which overlap is reported first. Static proxy overlaps need model validation
before being treated as physical CAD interference.

## 5. Camera-to-robot mapping and information boundary

The [native vision C ABI](../../Software/acvision/runtime/native_runtime.h)
accepts contiguous RGB bytes and provides orientation/reference validity,
homography, 64 occupancy/color candidates, optional foreground centroids and
800×800 rectified RGB. It has no simulator access. Python wraps each context
through `NativeVision`, with timestamps, identities and detached image arrays.
Expected chess kind comes from task/FEN context, not validated six-kind visual
recognition in the local manipulation pipeline.

The camera fixture uses 1920×1440 images, distance 1.05 m, azimuth 180°,
elevation −75°, and look-at `[0.245, 0, 0.012]`. Shared defaults live in
`virtual_camera.py`, with explicit experiment overrides. ArUco layouts belong
to the saved fixture. Board squares are 35 mm in this experimental model.

Current localization registers observed rectified RGB against empty/centered
reference images through [square_offsets](../../simulation/mujoco/src/atom_mujoco/board_piece_localization.py).
An image shift is converted to XY meters using square pitch and cell pixels,
with the rectified Y direction inverted. It is added to the static square
center supplied by the model. Board surface Z also comes from static model
geometry. Synthetic reference images are generated in separate scratch data.
This is camera-derived planar correction with experimental board-to-robot
calibration. Real image acquisition, intrinsics/extrinsics, TCP and height
evidence still require physical qualification.

C++ `CoordinateMapper` separately supports measured A1/H1 centers, pitch,
board rotation, rank direction and graveyard grids in millimeters. The native
training path instead supplies world points derived by Python. The new
hybrid contract must identify the single authoritative board/base transform,
its units, revision and validity, and invalidate plans after a reference change.
Homography alone supplies no measured gripper or piece Z pose.

The autonomous actor receives estimated source XY relative to FK of issued
commands. This FK uses static model geometry and command history, not live
joint measurements. Its source estimate can be remembered through occlusion,
with a visible flag and age expressed in frame counts. Board reference loss
and target visibility loss are currently distinct conditions. Define their
handoff/stop rules explicitly in M3/M4.

## 6. RL interfaces and learned behavior

The autonomous environment version is 3 and policy version is 2. It uses SB3
PPO MultiInputPolicy, a three-convolution image encoder, 256 projected visual
features with LayerNorm, and separate actor/critic networks with two
64-unit tanh layers. CUDA selection has an explicit failure path. Neural
updates and physics/collision/perception have separate backends.

| Actor input | Shape and provenance |
| --- | --- |
| `image` | 6×96×96 uint8, two rectified RGB frames |
| `task` | 4 normalized source/destination indices from logical task context |
| `commanded_joints` | 6 normalized issued commands |
| `command_history` | 12 values for two issued-command vectors |
| `visual_target` | 5 values for camera-estimated relative XY, commanded height over calibrated board, visibility and frame-age context |
| `object_context` | 8 logical kind/color one-hot values |
| `previous_action` | 7 normalized previous controls |
| `perception_valid` | 1 board-reference validity flag |
| `goal` | 3 objective flags for reach, grasp or lift |

The seven action components request Cartesian XYZ velocity, wrist velocity,
coupled opening velocity, elbow branch and persistent duration. XYZ rate is
limited by geometry/speeds and at most one square per maximum-duration action.
The current fixture allows one through ten 20 ms control intervals. Wrist and
finger commands are clipped to model travel. IK/speed projection tries scales
1, 1/2, 1/4, 1/8 and 1/16 before swept validation. Accepted results record scale
and final joint targets. Clipping and failed projection attempts lack a complete
structured transformation history.

These per-action bounds do not define a persistent authorized local workspace.
The policy can accumulate movements across decisions and select elbow branches.
No planner/RL ownership token or manipulation-only authorization exists yet.
The current randomized curriculum directly initializes admitted configurations
around the visually localized source. It does not execute a planned approach.

P038 residual policies instead use one 3-channel image, nominal phase,
commanded state, endpoints and previous residual action. Their wrist profile
has five residual controls and six commands. Their action meanings differ
from autonomous policies. Historical four-action pixel policies also differ.
Archive existence or timestep number cannot establish transfer compatibility.

## 7. Grasp, lift, reward and verification

The deterministic Playground performs preshape, descent, closure, grip check,
lift, transport, placement, opening and reconciliation. It uses `SceneFeedback`
to verify simulator contacts and piece state. Its completed outcome is explicitly
`COMPLETED_SIMULATION_ORACLE`. The local grab pose and lift distances include
existing experimental constants, so they require calibration/scope records.

`SceneFeedback.grip_contacts` checks both pads against the selected body.
`settled` checks modeled linear/angular velocity. Bilateral contact with a
resting piece is a grasp candidate. A stable lifted hold is separate evidence.
The contact predicate has no grip-force or force-closure verification, and
does not explicitly filter positive contact distance.

Autonomous feedback is separate from actor construction and uses the following
current components. Configuration-dependent values are identified explicitly.

| Component | Formula/value and source |
| --- | --- |
| Approach progress | Change in negative mean nonnegative pad distance divided by physical proxy height, from simulation geometry |
| Time/action cost | −0.01 per decision and −0.001 times squared normalized action norm |
| Rejected action | −1 with extra modeled penetration cost up to −5 |
| First bilateral-contact event | Configured grasp bonus, +2 in the audited fixture |
| First lifted event | Configured lift bonus, +3 in the audited fixture |
| Objective success | Configured +10 in the audited fixture |
| Non-target contact | Configured −20 per affected decision in the audited fixture |
| Neighbor displacement | Configured −1 per additional mm of peak excursion beyond the 0.25 mm dead band |
| Topple/failure/timeout | Configured topple penalty, default −50, failure −5 and timeout −5 |

`reach` approves mean clearance within the configured neighborhood, currently
35 mm. `grasp` approves bilateral contact plus settled motion. `lift` requires
bilateral contact, rise above one proxy height and ten stable qualifying
decisions in the fixture. Variable action durations make that dwell count
different from a fixed physical hold time. Discounting is currently per decision.

`CameraOnlyEnv` uses visual source/destination evidence, optional appearance
and neighbor checks, plus configured simulator contact/displacement penalties.
Its grasp/lift outputs remain unverified. The capture fixture has a documented
oracle execution mode and a separate camera inspection that can block before
motion. It does not establish camera-only grasp/release or graveyard occupancy
verification. The automatic Playground's PhysicalBoardState machinery is not
connected to autonomous policy episodes.

## 8. Known limitations and unresolved issues

1. Full wrist-compatible global planning/execution and explicit control ownership
   are absent across the automatic pathways. Reuse the existing native IK and
   controller while defining the new contract rather than creating another solver.
2. Current planner output supplies no alternative obstacle-aware global route.
   A validated starting state, approach region and all approach edges are needed.
3. Descent endpoint collisions are established in the experimental proxy model.
   Whether each overlap reflects physical CAD interference remains unresolved.
4. Deterministic capture currently loses grip in transport. Separate the contact,
   dynamics, controller and geometry explanations before extending the baseline.
5. The normalized training interruption has a joint-limit exception. Floating-point
   overshoot is reproducible in the old interpolator and its class has a regression
   correction. The exact old failed command was not saved, and a completed post-fix
   learning evaluation is still absent.
6. The older residual `_configure_nominal` assumes `_base`, `_stem`, `_head` and
   uses an incorrect generic box extent axis. The king has cross parts instead
   of `_head`. AutonomousScene avoids that dependency, but the residual path
   retains its limitation.
7. Autonomous contact/displacement stops are stricter than the earlier requested
   non-toppling penalty-only behavior. The structured supervisor must resolve
   this contract. Neither route has qualified physical recovery under ambiguity.
8. Rejection costs merge many IK/limit/speed failures into a generic cost. Depth
   distinguishes some collisions. No meaningful feasibility gradient is yet
   demonstrated for the other failure categories.
9. Camera-only grip/lift/held-pose verification and sufficiently current obstacle
   estimates remain open. Homography validity alone does not resolve occlusion.
10. Warm start copies compatible weights into a fresh optimizer. Checkpoints
    include Adam state, but exact RNG/environment/partial-rollout resume is absent.
11. Existing documentation has historical five-axis, RViz and calibration claims
    with different scope. Read this current audit before interpreting them as
    qualification of the latest wrist-capable model.
12. Firmware ships `configured=false`. The camera-only arm's issued commands
    remain estimates. Real J3/wrist mapping, servo conversion, homing, TCP and
    end-to-end motion require calibration and hardware tests.

## 9. Current tests, reports and compute evidence

Existing C++ tests ran through Ubuntu/WSL on the current `build/headless`
test tree. All 16 registered suites passed in 2.55 s. They cover vision
heuristics, board/chess operations, mapper/graveyard/task planning, protocol,
execution, IK and integration adapters. This was an existing binary build,
without reconfiguration or recompilation. It is not proof that every CMake
test target in the current source has been built or registered.

The Windows Python regression run exercised autonomous observation/supervision,
PPO graph/normalization, collision certificates, approach search, physical
state, real Chess Core requests, graveyard task plans, contact penalties,
full-board camera/FEN and native image ABI/CLI parity. Result **64 passed,
1 failed, 2 skipped in 59.64 s**. The skipped cases require the separate
`ATOM_CAMERA_ONLY_CONFIG` fixture. Native full-board, vision DLL and native
CLI inputs were configured explicitly for the exercised cases.

The failing capture case was rerun alone and failed again in 5.12 s with
`GRIP_LOST_DURING_TRANSPORTING`. It completed zero transfers while removing
`black_pawn_d7` from E3 to `graveyard:slot_0`. This reproduction establishes
the observed failure, without selecting a physical root cause.
[Full Python output](evidence-hybrid-m1/python-tests.txt),
[isolated capture output](evidence-hybrid-m1/capture-reproduction.txt).

Historical evidence was read again from the actual JSON files.

| Record | Measured outcome and scope |
| --- | --- |
| Main approach search, seed 100007 | 2,600 descent endpoint rejections, no swept trials or dynamic executions |
| Second-seed subset, seed 100008 | 312 descent endpoint rejections, no swept trials or dynamic executions |
| `reach-v3-watch-1794051936807` | 842 accepted segments of 1,024, 5/24 training reach successes, 2/4 final evaluation reach successes, zero grip/lift |
| `reach-normalized-1794052561762` | 227 recorded decisions, interruption on decision 228, 0/8 fresh-policy baseline reach successes, recovery archive, no final trained evaluation |
| Normalized CPU/CUDA diagnostic `cab474fa93844bc096eb8542a719f9b1` | Batch-64 median update 63.35 ms CPU versus 9.53 ms CUDA, about 6.65× for the neural microbenchmark, verified gradients/Adam changes and archive reload |

The CUDA result is historical diagnostic evidence for the normalized policy
architecture, not new training during M1 and not end-to-end simulator speedup.
The current inspection detects PyTorch 2.14.1+cu130, CUDA runtime 13.0,
SB3 2.9.2, MuJoCo 3.17.0 and RTX 5070 Ti. CPU collision/perception work remains
outside CUDA optimization. Policy inference, image preprocessing and complete
hybrid execution still need separately scoped timings on the eventual workload.

The root CMake cache points to a historical Windows source location. The
native `p038-core` cache points to the current repository but has testing off.
The headless cache is a WSL build. Calling Windows CTest on its Linux paths
fails discovery. Use WSL for that build and record new build identities when
fresh C++ qualification is performed.

## 10. Implementation plan and milestone gates

The latest roadmap's initial local skill is **grasp and lift**. Planned
transport, placement and retreat follow verified handoff. Earlier proposals
for learned placement remain a separate later experiment. A direct reproduction
of MoPA-RL's magnitude-based switching is also separate from this stage-based
hybrid baseline.

| Milestone | Coherent increment | Evidence required to report completion |
| --- | --- | --- |
| M1 — audit | This diagnosis, current tests and source/model evidence | Report current capability and blockers, then stop |
| M2 — planner qualification | Verify collision geometry/frame consistency, wrist-compatible model mapping, valid park and candidate local regions. Reuse native plan/IK, swept checks and controller to establish complete approach paths and alternative candidates. Check nominal carried-piece transport and retreat paths under declared hold assumptions | At least one complete nominal approach executed with wrist/model identity, enabled collision checking, observable rejection reasons and passing relevant regressions. Separate geometric transport admission from subsequent dynamic hold validation |
| M3 — planner/policy contract | Define bounded local workspace, six-command mapping, task identity, estimates/uncertainty, phase/owner/generation and returned proposal schema | Contract tests before policy execution, including wrong phase, stale scene, units, dimensions, hidden-state isolation and actual arrivals instead of teleportation |
| M4 — supervisor | Centralize phase/ownership authorization and reuse existing limit, IK, collision and dynamic guards. Log clipping/projection and precise rejection categories | Rejection without unsafe motion, perception/timeout/partial-execution handling, explicit recovery/reconciliation, resolved contact/penalty contract |
| M5 — deterministic grasp/lift | Establish repeatable local physical baseline from qualified planner arrivals and isolate the existing transport grip loss | Separate approach, grasp, lift, collision, timing, final pose and failure measurements over multiple seeds |
| M6 — local RL | Train only the qualified local manipulation skill with camera/task/command observations and separate simulator rewards | Independent held-out grasp/lift measurements against the frozen deterministic baseline, compatible checkpoints and finite updates |
| M7 — hybrid transfer | Return control after verified lift, plan held-piece transport/place/retreat, reconcile release and occupancy | Complete simulated transfers with explicit ownership history and physical/visual evidence distinguished |
| M8 — generalization | Balanced shared object-conditioned curriculum, neighbors and measured/provisional perturbations with provenance | Per-object held-out outcomes, retention and complete-task metrics |
| M9 — Playground/dashboard | Expose real owner, phase, trajectories, action transformations, feedback and training metrics | Backend-driven UI and tested controls, after core controller qualification |

Preserve checkpoints, reports and code versions at each gate. Freeze the
success definition and matched scenarios for comparisons. Label simulation
oracle results, camera evidence, learned performance and hardware qualification
separately. Implementation and training begin in their respective later
milestones after the required report and instruction to advance.

## Reproduce the M1 checks

Run from the repository root in PowerShell. These are regression tests,
without a training loop or hardware actuation.

~~~powershell
wsl -d Ubuntu -- ctest --test-dir <repo>/build/headless --output-on-failure
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$env:ATOM_AUTONOMOUS_CONFIG = (Resolve-Path 'simulation/mujoco/training/camera-manipulation/runs/pawn-e2-e4-vision-fen-v1/environment.json').Path
$env:ATOM_CAMERA_FEN_CONFIG = $env:ATOM_AUTONOMOUS_CONFIG
$env:ACVISION_RUNTIME_DLL = (Resolve-Path 'build/p038-core/bin/Release/acvision_runtime.dll').Path
$env:ACVISION_PERCEPTION_EXE = (Resolve-Path 'build/p038-core/bin/Release/perception_image.exe').Path
& $py -B -m pytest -p no:cacheprovider -q -ra `
  simulation/mujoco/tests/test_autonomous_manipulation.py `
  simulation/mujoco/tests/test_ppo_dashboard.py `
  simulation/mujoco/tests/test_collision.py `
  simulation/mujoco/tests/test_approach_sweep.py `
  simulation/mujoco/tests/test_physical_state.py `
  simulation/mujoco/tests/test_chess_commands.py `
  simulation/mujoco/tests/test_task_plan.py `
  simulation/mujoco/tests/test_contact_supervision.py `
  simulation/mujoco/tests/test_camera_only.py `
  simulation/mujoco/tests/test_native_runtime.py
~~~

The recorded run sets PyTorch CPU threads to two. Native-runtime tests use
the existing P036 image at
`simulation/mujoco/examples/compare_perception_reproductions/runs/p036/p034-repeat/initial-270-45.png`
and ArUco layout v4 by default. These generated fixtures, DLLs and WSL binaries
are local prerequisites. A new checkout requires their documented preparation.
The inspection JSON records the actual selected motion/vision DLL and model
hashes. The legacy untracked script remains outside these checks.
