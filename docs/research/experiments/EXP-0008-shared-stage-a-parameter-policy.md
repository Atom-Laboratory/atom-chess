# EXP-0008 — Shared Stage A parameter-policy learning

Date: 2026-11-21. Decision: S061. Algorithm: expert mean BC, followed by clipped
PPO for a one-step contextual bandit. This is learning over planner parameters,
not arbitrary low-level trajectories or sequential visual servoing.

## Hypothesis and controlled scope

Can one shared policy reproduce the verified isolated grasp while improving
command timing within the same constrained parameterization? The actor sees
12 normalized features: ac:vision-derived source XY, six issued entry commands,
and four logical source/destination square coordinates. It does not receive
actual joint/object position, velocity, contacts, reward or success. Static
compiled command limits normalize command history; this is not encoder feedback.

The 10,247-parameter PyTorch actor/critic uses separate 64/64 Tanh MLPs, a
three-dimensional tanh-Gaussian action and an immediate-reward critic (gamma=0).
BC fits the original hash-bound CEM expert mean for 100 Adam epochs at .003.
PPO uses Adam .0003, clipped ratio .2, normalized batch advantages, value MSE
coefficient .5, base-Gaussian entropy coefficient .001 and gradient norm .5.
At most four optimizer passes are allowed; approximate KL above .03 stops further
passes. The Jacobian of tanh and the affine action map is included in log density.
Reported entropy is explicitly the base Gaussian's differential entropy.

Parameters are the existing closing-load factor [1.5,4], finger speed fraction
[.1,.5] and local lift-rate fraction [.1,.5]. Native ac:motion still generates and
screens the complete close/settle/lift/hold path. Geometry, contact masks, friction,
mass, gains, camera, wrist and grasp height are unchanged. Every successful macro
episode must physically lift and sustain bilateral contact for one second.
Invalid geometry, prohibited contact or a failed physical criterion receives
-100; success receives 10 minus bounded duration/slip costs. Physics truth is
privileged reset/reward/safety/evaluation data, never actor target coordinates.

## Measured results

Sampling seed 970400. One training entry (970200); excluded validation entry
970201. Eight independent physics worlds sample one shared policy per update.

| Update | Macro training episodes | Physical held lifts | Mean reward | Batch evaluation wall | Gradient update wall |
| --- | --- | --- | --- | --- | --- |
| 1 | 8 | 8/8 | 9.49513 | 18.67 s | .016 s |
| 2 | 8 | 8/8 | 9.51068 | 17.99 s | .019 s |
| 3 | 8 | 8/8 | 9.50480 | 18.93 s | .023 s |
| 4, optimizer/RNG checkpoint continuation | 4 | 4/4 | 9.49546 | 17.87 s | .278 s |

The first run took 110.32 s including imports, BC, three GPU batches and
deterministic pre/post GPU/CPU checks. The continuation took 65.41 s including
its own setup and paired evaluation. Presentation/export runs are timed
separately. This is not GPU-resident end-to-end RL: small PyTorch updates used
CPU, while a version-isolated CUDA subprocess executed batched physics.

Both training and excluded validation references passed canonical CPU/GPU checks
before and after PPO. The BC-initialized policy already worked; this experiment
does not establish an improved success rate caused by PPO.

| Deterministic mean policy | Training Stage A duration | Excluded validation duration | CPU held-lift outcome |
| --- | --- | --- | --- |
| BC warm-start | 16.094 s | 16.094 s | Both passed |
| After update 3 | 15.028 s | 15.028 s | Both passed |
| After resumed update 4 | 14.832 s | 14.832 s | Both passed |

The 1.262 s (7.84%) decrease from the BC mean is a measured timing change on
these two entries, not a broad efficiency/generalization result. The best earlier
frozen CEM candidate took 14.624 s on the validation entry, so this does not
establish an advantage over the best retained CEM timing.

## Additional frozen test

A fresh canonical reference on seed 970202 completed native camera localization,
physical entry and the independent deterministic held-lift diagnostic. Its signed
source XY was [.26355,-.08785] m. The checkpoint from update 4 then selected
parameters without training or optimization on this reference. GPU and CPU both
passed; CPU minimum held rise 43.793 mm, maximum hold drop .312 mm, one-second
bilateral hold, no forbidden engine contacts. Stage A duration was 14.832 s;
the bounded inference/evaluation process took 21.98 s.

The same reference was first tested with the update-3 checkpoint and then with
update 4. These are repeated policy comparisons on **one** additional entry, not
two independent test starts. Source offsets remain approximately the fixture's
1 mm jitter. EXP-0006 retains the failed first seed-970201 camera entry; a
conditional successful reference cannot erase that end-to-end failure.

## Artifacts and reproduction

Use [the module README](../../../simulation/mujoco/accelerated/README.md#shared-stage-a-bcppo-parameter-policy-pilot)
for the complete PowerShell block, budgets, source-matched optimizer/RNG resume,
excluded-reference evaluation and Watch. The default training CLI exports an
accepted final command sequence and opens a separate finite CPU replay; it does
not portray that replay as live optimizer sampling. Two complete default replay
cycles were recorded with no interruption or native viewer crash.

[Raw reports, losses, episode CSV and FIG-0004](../../../simulation/mujoco/accelerated/reports/EXP-0008)
are tracked. Full physics tapes, checkpoints and immutable executed sources remain
in the named fresh local run directories. Latest verified checkpoint:

`accelerated/runs/EXP-0008/RUN-shared-parameter-resume-2644d927be2b4f83936aee61708f8862/policy.pt`

SHA-256: `f56f6e2d0c0e36539cc78748393b8e5d39b6578692b5fbe13ef668ff01ee9428`.
An identical 143,625-byte copy is tracked as
[`policy-update-4.pt`](../../../simulation/mujoco/accelerated/reports/EXP-0008/policy-update-4.pt)
so the small verified policy/optimizer artifact is available with the research
package; large physics archives remain in ignored runs.
Do not confuse this file with older camera/reach PPO ZIP checkpoints: their
observation/action schemas and objectives differ.

## Limits and next gates

Only one training context, one excluded validation context and one additional
camera entry were tested. Parallel episodes vary parameters, not target identity
or obstacle layout. There is no demonstration of a policy learning to choose
arbitrary approach directions, wrist orientations, grasp heights or transfers.
The original wrist axis is preserved in planner commands; these three policy
outputs do not learn wrist control. Initial states are restored from physically
executed entries, rather than independently approached by this parameter policy.

Occupied-board entry remains geometrically rejected in the retained search
space. More isolated episodes cannot solve a path that the planner disallows.
Sparse-neighbor feasibility, broader camera/task variations and a qualified
online visual outcome verifier precede any claim of general manipulation or
hardware deployment. No original local-policy admission lease is bypassed.

References: [PPO](https://arxiv.org/abs/1707.06347),
[PyTorch distributions](https://docs.pytorch.org/docs/stable/distributions.html).
