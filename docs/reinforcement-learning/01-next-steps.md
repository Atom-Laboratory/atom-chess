# Next engineering steps: from lift to camera-guided chess manipulation

Current camera-guided implementation and test commands are in the
[MuJoCo README](../../simulation/mujoco/README.md). The material below records the
earlier v3 study baseline or its theoretical foundations.

This is a proposed implementation sequence. Only the two local curricula and
training tools in [the current-system page](00-current-system.md) are implemented.
The gates below are development targets, not achieved results or guarantees.
Every architecture change requires an ADR, one coherent implementation, tests,
reviewed evidence and a separate commit. Do not change a running experiment's
meaning by editing its reward or task and retaining its label.

## The immediate next increment

Build a **standalone frozen-checkpoint evaluator** for version-3 lift. The current
trainer evaluates only a few fixed seeds at the end of a run; replay provides
one episode. Neither is the broad qualification harness described here.

Inputs should identify checkpoint/hash, model bundle/hash, environment version,
curriculum, seeds, reset-distribution version and output directory. Outputs should
include per-episode outcomes, duration, maximum lift, grip retention, bystander
translation/rotation, failure stage and aggregate uncertainty. The evaluator must
never optimize parameters, overwrite the checkpoint or commit official chess state.

Tests should prove that policy parameters remain unchanged, seeds are respected,
failures count in the denominator, incompatible models are rejected, and a failed
or interrupted experiment cannot be silently reported as a clean evaluation.
A fixed script that simply lifts is a useful comparison for this curriculum;
it is not a deployable visual policy. Compare it with hold and learned inference.

**Why this comes first:** a lift task starting with prepared contact can be solved
by a nearly constant upward command. High success may prove controller learning
without proving useful dependence on the camera. Evaluate that distinction before
making the task bigger or the network more complicated.

## Implementation gates and proposed criteria

| Gate | Work and responsible modules | Evidence needed to move forward |
|---|---|---|
| G0: reproducible baseline | Freeze run/config/checkpoint; record resolved PPO defaults, camera, timestep and hardware | A reconstructible run, matching hashes, explicit result scope and failure accounting |
| G1: local lift evaluation | Standalone evaluator, independent training seeds, reset seeds and oracle checks | Proposed: >=95% lift success across >=300 frozen evaluation episodes; zero >8 mm bystander displacements in that suite; include uncertainty and per-seed results |
| G2: visual-dependence audit | Black/constant frame, stale frame, crop occlusion and temporal tests; compare an open-loop upward policy | Evidence that the intended visual information improves behavior under genuinely variable initial conditions, not just under one scripted reset |
| G3: local grasp | Current grasp stage plus diagnostic failures and reset audits | Bilateral grasp, 35 mm lift, retention, no disturbance; proposed same simulation evaluation target as G1, separately measured |
| G4: multiple pieces and local goals | Parameterize identity, source, grasp height and goal; add appropriate goal representation and geometry evidence | Held-out piece types, colors and local offsets; clearance checked across actual proxy dimensions; no claim that pawn success covers knights/kings |
| G5: verified pick/place | Phases for approach, grip, lift, transport, support, release and retreat; geometric planning plus local policy | Full swept plan plus live checks; pose/support/release and all bystanders verified; state updates only after completion |
| G6: complete task integration | ac:chess -> existing task adapter -> ac:motion/Motion Intelligence -> controller; capture removal and Graveyard | Legal moves, captures, castling decomposition, occupied-slot rejection and recovery sequences through the real integration interface |
| G7: ac:vision feedback | Timestamped calibrated board observations, piece/tool estimates, uncertainty and loss-of-visibility handling | No simulator ground truth in the deployed observation/verifier path; measured errors, latency, coverage and explicit unknown states |
| G8: calibrated sim-to-real | Measured geometry, axes, actuator response, delays, friction/mass uncertainty; fit/validate separately | A mismatch report on data not used to fit parameters; real and simulated observation/action units reconciled |
| G9: supervised hardware skill | Independent stop/watchdog/limits; deployment profiling; one isolated piece at low speed | Repeated measured physical outcomes and failure handling; no unbounded online exploration or automatic promotion from simulator reward |
| G10: reliable chess operations | Sequences, captures, fixed home Graveyard slots, recovery and logical/physical reconciliation | Full-episode and long-sequence error rates, bounded recovery, no false chess-state commits |

G1/G3's numerical targets are proposed experiment planning thresholds, not a
safety standard. With zero failures in 300 independent trials, the approximate
one-sided 95% upper failure bound is still about 1%. Repeated highly correlated
resets weaken that interpretation. Hardware deployment needs a separate
risk-appropriate acceptance protocol; no simulation percentage supplies one.

## G1 design details

Use at least several independent training seeds before making an algorithm-level
claim; five is a practical initial plan, not a universal sufficient sample size.
A single policy tested on 300 reset seeds estimates that checkpoint's behavior,
not variability caused by training. Keep separate sets for development, checkpoint
selection and final reporting. If the same test seeds are repeatedly inspected
while tuning rewards, they have become validation data.

The current randomization is small and only changes the starting arm joints.
An evaluator must distinguish performance within that narrow distribution from
new tests with different offsets, lighting, camera parameters or dynamics. Those
new variations are not implemented environment flags today. Version them before
use, preserve successful and unsuccessful episodes, and report confidence
intervals per training seed as well as aggregates.

Record actual contact-related metrics, not merely the final success flag. A
piece can be touched, rotated or moved less than 8 mm without triggering the
current disturbance predicate. A policy must not gain credit from moving pieces
and returning them approximately to their original positions before the last
frame. Maximum intermediate displacement and contact events belong in the future
step-level evaluator.

## G2: ask whether pixels matter

Compare normal observations with a constant image, delayed images and selective
occlusion while holding the physics/reset seeds fixed. Distinguish a policy
trained without useful vision from a trained policy suddenly facing a corrupt
sensor; the latter tests robustness, not the former's optimal performance.

Vary starting TCP alignment and target location so the correct action differs
across episodes. If every successful episode just needs Z-up, the environment
cannot establish rich visuomotor competence. Add temporal information only after
showing the missing state matters. Frame stacking or a recurrent policy changes
the observation/checkpoint contract and requires a versioned experiment.

## G3: learning the actual grasp

Start grasp with WarmStart to copy a saved lift policy into a new training run.
Use Resume to continue an identical task. Match the bundle, version and horizon.
Compare transferred and fresh initialization under the same evaluation protocol.

Diagnose failures by phase: bad alignment, low grasp, premature closure, slipping,
neighbor contact, insufficient lift, or unstable reset. A failed reset is an
environment problem to report, not a successful learning episode. Determine
whether additional sensors, memory or a different action representation are
needed before simply increasing the training budget.

## G4-G6: from one local skill to chess tasks

The target external command remains `MOVE(source_square, target_square)`. Chess
Core decides legality and special-move semantics. Physical identity is resolved
from confirmed physical occupancy, not required from the caller. Captures remove
the victim to its assigned Graveyard location before transporting the attacker.
The 16 slots per color and their two-by-eight layout must appear in geometry,
planning, occupancy and reconciliation, including already occupied slots.

A proposed goal-conditioned policy could receive calibrated image crops plus
source/target masks or a structured goal vector. That would no longer be the
current RGB-only single-pawn interface. Define the representation, coordinate
frames and deployment observability first. Do not append simulator piece poses
and keep calling the observation camera-only.

Prefer evaluating a hybrid first: conventional planning supplies an obstacle-aware
nominal path and a bounded learned correction handles local alignment and grasp.
The current trainer does not implement residual control. Both nominal and
corrected commands must pass supervision; a correction can invalidate the
nominal collision clearance. Recovery preserves last confirmed occupancy and
records uncertainty rather than guessing a successful state.

## G7: specific ac:vision integration work

Existing [BoardDetector](../../software/acvision/include/board_vision/board_vision.hpp)
estimates board corners; [PieceDetector](../../software/acvision/include/piece_detector/piece_detector.hpp)
classifies occupancy/color. [BoardObservation](../../software/acvision/include/board_observation/board_observation.hpp)
contains an 8x8 EMPTY/WHITE/BLACK array, not calibrated 3D poses or contact sensing.

A new adapter/contract needs capture timestamps and sequence numbers, frame IDs,
calibration IDs, confidence/uncertainty and unknown/occluded states. Separately
specify how to track physical piece identities, tool position, held-piece motion,
support and release. Preserve the existing distinction between observation and
official chess state. A robot's own motion must not be misinterpreted as a human
legal move before reconciliation.

Train/test on rendered and real frames with matched camera geometry. Include
an unseen board and re-calibration test before claiming the future physical
board works automatically. Board corners or fiducial markers can anchor a frame;
they do not reveal every elevated or occluded object's pose.

## G8-G10: no-encoder hardware implications

The user-described arm has a fixed camera but no measured joint encoders or grip
sensor. Simulator joint state and bilateral contacts therefore have no direct
hardware counterparts. Step/pulse counts are estimates; missed steps, backlash
and compliance can make them wrong. A fixed camera may lose the fingertips behind
the piece or wrist. Specify when the system must stop or retreat because the
relevant state cannot be observed. Do not interpret a missing detection as an
empty square or a successful release.

The real controller needs calibrated pulse/angle or servo mapping, zeros, limits,
startup reference, communication acknowledgment and local fault handling. Visual
feedback can supervise and correct observable error at a suitable rate, but
cannot replace every low-level state measurement by assertion. If the required
observability/reliability cannot be demonstrated, change the camera placement,
add a view or instrument the mechanism. See [robotics and transfer](04-robotics-and-transfer.md).

## Proposed commit sequence after this documentation

1. ADR and frozen evaluator with measured metrics and immutable checkpoint checks.
2. Observation-dependence ablations and a simple open-loop baseline.
3. Grasp failure traces and a versioned broad reset/evaluation distribution.
4. Goal/piece/task contracts, then generic manipulation with collision supervision.
5. Timestamped acvision observation adapter and camera-calibration evidence.
6. Hardware-calibrated backend and supervised deployment qualification.

These are future increments. This documentation change does not implement them,
change the running trainer, or enable RL in production chess execution.
