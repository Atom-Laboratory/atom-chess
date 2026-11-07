# Autonomous reach pilot evidence

## Watched policy before visual normalization

Run `simulation/mujoco/training/autonomous-manipulation/runs/reach-v3-watch-1794051936807`
completed 1,024 additional decisions from the verified 512-decision checkpoint
of the preceding pilot. Warm start copied weights into a fresh optimizer.
This experiment used environment version 3 and the original unnormalized
policy architecture. The learning rate was 0.001, rollout size 128, minibatch
size 64 and five epochs per rollout. The scene contained one pawn, source
E2 and task destination E4, with the original full-gripper contact geometry.
The objective was reach, with a 35 mm mean pad clearance threshold.

| Measurement | Result |
| --- | --- |
| Accepted nominal segments | 842 / 1,024 |
| Velocity rejections | 103 |
| Swept collision rejections | 35 |
| IK/limit rejections | 44 |
| Completed training episodes | 24 |
| Training reach successes | 5 |
| Training time limits | 19 |
| Initial held-out reach successes | 1 / 4 |
| Final held-out reach successes | 2 / 4 |
| Bilateral grips | 0 |
| Lifts | 0 |

The held-out seeds were 910000 through 910003. The initial policy already
contained transferred pilot weights. It is not a fresh random baseline.

| Seed | Initial policy best gap (mm) | Final policy best gap (mm) | Final result |
| --- | --- | --- | --- |
| 910000 | 36.18 | 33.36 | Reach threshold crossed |
| 910001 | 52.73 | 53.05 | Time limit, final gap 106.81 mm |
| 910002 | 34.87 | 34.26 | Reach threshold crossed |
| 910003 | 80.11 | 80.80 | Time limit, final gap 109.34 mm |

The pilot does not qualify reliable approach or manipulation. Its increase
from one to two successes is based on four episodes. Two cases end farther
away. Reaching the region does not establish contact, grasp, lift, E2-to-E4
transfer or generalization to neighboring pieces.

## Numerical diagnosis and next controlled experiment

The persisted dashboard activations show projection RMS rising from about
3.90 to 11.86. First-layer actor tanh RMS rises from about 0.94 to 1.00 and
critic tanh RMS from about 0.95 to 1.00. The final explained variance is 0,
with value loss about 49.8. These measurements show saturation and weak value
prediction. They motivate the next architecture correction. They do not
establish that saturation alone caused every failed motion.

S026 adds LayerNorm to the visual encoder output and a separate policy
version. It restores the 0.0003 learning-rate baseline and introduces a
configurable 0.03 target KL. A fresh normalized policy and new experiment
records are required. Historical failed archives remain available.
[Decision and alternatives](../../simulation/docs/adrs/S026-normalize-autonomous-visual-features.md)

## Qualification before a longer run

The first normalized attempt,
`reach-normalized-1794052561762`, recorded 227 training decisions before
a joint-limit exception during decision 228. Its fresh-policy baseline
had zero reach successes on eight seeds, 910100 through 910107. There is no
final trained evaluation for this interrupted run. The recovery archive and
its SHA-256 sidecar are preserved.

The first recorded PPO update had explained variance about 0.053, compared
with the previous pilot's near-zero final value. This single update does
not qualify improved learning. The actual policy CUDA diagnostic passed
finite gradients, Adam parameter changes, and policy/optimizer reload.
Its batch-64 median update times were about 9.53 ms on CUDA and 63.35 ms
on CPU. These timings exclude simulation, rendering and collision checks.

Endpoint interpolation can reproduce small floating-point limit overshoots
with otherwise valid endpoints. A regression now bounds interpolation by
its validated endpoints, while retaining strict joint validation. Future
failure records also include the pending action and interval. The interrupted
run did not record its exact rejected command, which limits diagnosis.

The current training direction recommendation is
[planned travel with learned local manipulation](hybrid-motion-learning.md).
It requires its own feasible handoffs and skill evaluations.

The named curriculum must pass finite CUDA updates and checkpoint reload,
stable repeated resets, policy isolation, correct reward signs and collision
supervision. Compare its initial and final policies on held-out configurations
and retain an additional final seed range. Record success counts, best and
final distances, return components, rejection types, contacts and failures.
A larger random-start radius and the full initial chess board need separate
evaluations. Stable grip, lift, transport and placement require their own
criteria before extending overnight training to those tasks.
