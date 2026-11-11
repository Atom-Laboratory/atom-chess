# M4 local supervision and experimental training status

Current status recorded on 2026-11-09. Read
[S031](../../simulation/docs/adrs/S031-local-proposal-supervision.md) and
[S032](../../simulation/docs/adrs/S032-experimental-camera-actor-ppo.md).

## Implemented simulation adapter

`LocalSupervisor` connects the five-control M3 proposal to existing native IK,
AutonomousControl swept checking and MotionController. Projection is disabled.
Declared bounds/rates must match the selected six-command wrist-aware model.
Before execution it checks task/phase ownership, model/controller/scene identity,
fresh native perception, board reference, measured tracking and the complete
proposed local path. Runtime guards detect unexpected contacts, toppling,
displacement, joint excursion, perception expiry, grip loss and settling timeout.
Partial failures require reconciliation and prevent further commands.

RL execution requires an admitted LocalHandoff and a hash-bound workspace
artifact that matches numeric limits/model/task/reference and references
successful grasp/lift baseline reports. No actual qualified workspace artifact
has been produced. Unit tests exercise this interface with explicitly synthetic
assertions; those are not manipulation evidence.

A separately labelled deterministic qualification lane can execute individually
checked actions after an actual matching M2 approach without retreat. It cannot
grant an RL lease or set training eligibility. This permits diagnosis of physical
feasibility without pretending that the full workspace is qualified.

## Contact settling and performance corrections

The first head-closure attempt timed out because a generic position rule tried
to drive fingers through a rigid held piece. The adapter now distinguishes
stable bilateral selected-pad contact from arm tracking failure. Positive finger
position error can be accepted only with force-limited actuators and deflection
bounded by compiled force range divided by position gain. Arm/wrist tolerances,
joint limits, full hull geometry and other collision checks remain unchanged.
This is independent simulator safety feedback, not actor proprioception or a
physical force measurement.

The supervisor reuses the validated camera frame immediately before execution
when its age is still within the existing bound and the scene/model/ownership
checks still pass. If preflight outlives that bound, it captures another frame.
Runtime execution also stops on frame expiry. Capture/reuse counts are logged;
this removes a duplicate vision pass, not camera validation.

## Actual diagnostic results

All local paths below are under
`simulation/mujoco/examples/qualify_hybrid_approach/runs/`.

| Trial | Local run | Observed outcome |
|---|---|---|
| Full board, stem | `b06a27a381ed42ffab44166fc354c258` | Approach and small local probe executed; descent screen rejected hand-hull/D2-pawn intersection |
| Isolated pawn, stem | `4aa7651cc85844cf8c55cf4b18966cca` | Descent executed; closure screen reached the existing 1 mm margin against the selected pawn head |
| Head, before contact-settling correction | `236521e3cba047bab7765eaedef866b0` | Closure reached contact, then generic settling timed out |
| Head, original closing preload | `a9e0347ffa474d9e96ec29f9f6150196` | Grasp recorded; bilateral contact lost during attempted lift |
| Head, load factor 2 | `7ea4b500b3fd436ebe51081d0eb7fcdd` | Stronger closure screen violated the unchanged selected-hull clearance; not executed |
| Head, load factor 1.5 | `f9eba41b00b441c89268112580a9abf7` | Grasp recorded; lift failed with GRIP_LOST_DURING_LIFT |
| Head, load factor 1.65 | `cdc6f83fb1234f8bbb20e833bb6a4e83` | Grasp recorded; lift failed with GRIP_LOST_DURING_LIFT |
| Head, factor 1.65, lift fraction .25 | `89311a26a91c4f5683d1b6dd55fb58eb` | Grasp recorded; slowed lift still failed with GRIP_LOST_DURING_LIFT |

The last trial took 291 local decisions and 24.15 seconds of diagnostic wall
time. Its measured final upward piece displacement was only 0.0181 mm.
It is **not** successful elevation. No clearance, collider size, contact mask,
piece mass or controller gain was changed to turn a rejected trial into a pass.
Grasp-height and preload targets are explicitly experimental choices derived
from existing model primitive centers/radii and a static load approximation.
Neither simulated contact nor commanded position establishes hardware success.

The [example README](../../simulation/mujoco/examples/qualify_hybrid_approach/README.md)
documents Watch, qualification flags and output files. Results preserve plan and
runtime identities, rejected pairs, actual motion traces, images, final state
and exception records. These are local ignored artifacts, not promised assets
in every source checkout.

## Training authorization and separation

After these failures the operator explicitly requested learning anyway, limited
the deployed sensor to camera, allowed simulator training supervision and asked
for background 2→4→8 comparisons. S032 records this changed experimental scope.

The running experiment uses the **existing seven-action autonomous PPO runner**,
not this five-action hybrid execution adapter. The CUDA pilot changed weights,
saved/reloaded its policy with verified hashes and scored 0/2 on grasp evaluation.
It is the source for independent background policies; incompatible older feature
architectures were not silently resumed. The camera/hidden-state invariance
integration test passed using the actual native full-board fixture.

Read the [training README](../../simulation/mujoco/training/autonomous-manipulation/README.md)
for the bounded parallel session, per-worker checkpoints/CSV, resource gates,
validation-based escalation and after-round STOP file. This authorization does
not convert failed deterministic manipulation into hybrid qualification, prove
RL improvement or establish readiness for hardware.

## Remaining hybrid gates

Repeatable grasp/lift, a justified local workspace artifact, actual camera-only
outcome verification, carried-object transport/placement, full-board access and
physical calibration remain open. The historical capture regression
`GRIP_LOST_DURING_TRANSPORTING` also remains open. Training success must be
evaluated separately from held-out manipulation and physical deployment.
