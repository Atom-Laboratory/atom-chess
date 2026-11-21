# EXP-0006 — Isolated Stage A CEM command search

Date: 2026-11-21. Decisions: S058/S059. Method: bounded diagonal-Gaussian CEM,
not neural-network training. Baseline: the EXP-0004 camera-localized executed
near-grasp entry at e2, seed 970200. Canonical physical inputs remain unchanged.

## Question and defined pilot

Can parallel command-space evaluation find a close/lift/hold plan that also
passes canonical CPU replay? Three parameters vary: load factor [1.5, 4.0],
finger-speed fraction [.1, .5] and local-lift-rate fraction [.1, .5]. Bounds
refer to existing compiled gains/rates and model-derived preload, not measured
hardware force. Source XY, wrist and grasp height remain from the camera/native
reference. No friction, mass, collider, actuator gain or contact mask is optimized.

Complete closure/carried-lift paths pass native IK, force/travel/velocity limits
and independent sweeps before simulation. Each accepted candidate includes
closure, settling, lift and one-second hold. Validity and physical success rank
ahead of height/time. Physics truth initializes worlds and evaluates outcomes;
it does not supply target XY. This does not solve park-to-transfer planning.

## Results

[EXPERIMENTAL-EVIDENCE] Sampling seed 970300, population eight, two generations:

| Generation | Geometrically accepted | Physically passed held-lift criteria |
| --- | --- | --- |
| 0 | 8/8 | 7/8 |
| 1 | 8/8 | 8/8 |
| 2, resumed distribution/RNG | 8/8 | 8/8 |

The first 16 evaluations plus canonical winner replay took 45.95 s wall time;
the resumed eight evaluations took 20.06 s. These include setup, path filters,
GPU evaluation and final CPU replay, and differ from physics-only throughput.
Some candidates repeat the retained best; these counts are not independent
generalization or reliability trials.

The generation-1 winner used load factor 2.98428, finger-speed fraction .20277
and lift-rate fraction .34788. Its Stage A command sequence lasted 14.0 s.
Canonical replay minimum rise during hold was 44.110 mm; maximum hold drop
.312 mm; bilateral contact and settling criteria held, with no prohibited
engine contact. A resumed winner also passed canonical replay. No claim of
advantage over random/grid search or PPO is established by this pilot.

A later four-member/two-generation run bound reference report/handoff hashes
explicitly and verified source XY against the signed camera plan. It passed
4/4 then 4/4, with canonical winner verification. Large accepted tape/physics
NPZ and per-generation health remain in local runs; small metrics and summaries
are [archived here](../../../simulation/mujoco/accelerated/reports/EXP-0006).

## Failed launches and evaluation selection

The first launch failed before physics due to an unnecessary Pillow import in
the shared geometry helper. S059 extracted that exact function unchanged into
the non-rendering core package. This was a dependency failure, not a physical
failure or a reason to change the GPU environment's physics.

An independently seeded native reference attempt (970201) stopped during
descent with `PERCEPTION_EXPIRED_DURING_EXECUTION`, before creating a verified
near-grasp entry. The frozen-parameter evaluator correctly rejected it. That
pipeline failure remains archived and must not be silently omitted from a future
end-to-end success denominator. A same-seed headless retry investigates execution
timing; graphics contention is a hypothesis, not a demonstrated cause.

## Artifacts, reproduction and limitations

Use [the GPU README](../../../simulation/mujoco/accelerated/README.md) for bounded
CEM, fresh outputs, matching-input checkpoint continuation and frozen-parameter
evaluation. Generation JSON and candidate CSV preserve negative outcomes.
Checkpoints save distribution/RNG, not a neural policy or live physics process.
Source snapshots capture precommit CEM code over 2d1bf19. Shared physical sources
and runtime hashes are recorded in later reports. Original prototype checkpoints
predating stricter reference binding remain attributable to their executed source.

No held-out task success is claimed here yet. Start variation is approximately
the prepared fixture's 1 mm jitter, not arbitrary board movement. Occupied-board
entry, generic transfers, camera-only outcome verification, demonstration actor
observations, BC/RL and hardware calibration remain open. CEM success does not
grant the original manipulation-policy admission lease.
