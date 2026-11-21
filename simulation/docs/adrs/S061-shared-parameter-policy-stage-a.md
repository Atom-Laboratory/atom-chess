# S061 — Shared PPO parameter policy for the isolated Stage A planner

**Status:** Accepted (bounded research pilot; not production policy admission)

**Date:** 2026-11-21

**Decision owners:** Motion planning, reinforcement learning, experiment verification

**Related experiments:** EXP-0008

**Related findings:** RF-0001, RF-0003

**Supersedes:** None

### 1. Context

The native planner plus bounded CEM can execute and hold an isolated pawn. Two
camera/command demonstrations reproduce exactly on canonical physics. Learning
arbitrary trajectories from scratch would discard that working geometry and
confound physics feasibility with exploration. Crowded insertion remains open.

### 2. Evidence

EXP-0006 verified load/closure-rate/lift-rate parameters on canonical CPU and GPU.
EXP-0007 establishes camera-source and issued-command provenance. The existing
reach learner uses PPO. None of those measurements establishes a learned grasp
or a reason to replace that algorithm with SAC, HER or an independent policy per
environment.

### 3. Decision

Implement a **shared contextual parameter policy**, initially one macro-action
per episode. The action chooses the same three bounded CEM command parameters;
native ac:motion still constructs and screens complete close/lift/hold paths.
This is a one-step contextual bandit trained with PPO's clipped policy objective,
not a new sequential visual servo controller. Do not label macro episodes as
low-level control timesteps or as a solved general manipulation task.

Actor inputs are signed native-camera source XY, normalized issued/planned entry
command and source/destination squares. No measured qpos/qvel, contact, object
pose or simulator success flag enters the actor. These are ac:vision features,
not a CNN over raw RGB. The existing full-frame/command dataset remains available
for future temporal image policies. Entry perception is frozen for this pilot.

Warm-start the actor mean by behavior cloning the original verified CEM expert's
three parameters. Keep validation reference identity distinct and exclude it
from BC and PPO updates. Use one shared MLP actor/critic and a tanh-transformed
Gaussian, including the log-density Jacobian. The critic predicts immediate
episode reward (gamma=0); there is no fabricated temporal bootstrap.

GPU worlds evaluate independent parameter samples through the same geometric
filters, command limits and physical criteria as CEM. Simulation truth provides
reward/safety/outcome only. Invalid geometry, forbidden contact or a failed held
lift receives -100; successful physical episodes receive 10 minus bounded
duration/slip costs. A scalar reward can never declare physical success.

Retain separate environments: canonical PyTorch performs small shared-policy
updates; a bounded MJWarp subprocess evaluates batches. This deliberate initial
host/process boundary preserves the established environments and source isolation.
Measure its overhead; do not claim GPU-resident end-to-end RL or speedup.

### 4. Alternatives considered

CEM without a policy remains the baseline. Direct trajectory PPO, SAC with replay
and image-conditioned BC need broader demonstrations and online observation
qualification. HER has no justified relabeling semantics for contact constraints
in this pilot. A constant expert is an essential comparator, not learned
generalization. Independently training a network in every world wastes data.

### 5. Technical rationale

Learning a small planner parameterization tests shared updates, physical rewards
and independent evaluation while retaining a verified physical reference. It
cannot discover arbitrary approach/wrist/height strategies outside those bounds.
Full occupied-board feasibility cannot be repaired by more macro-policy episodes.

### 6. Implementation

Add camera-context/actor/critic/loss helpers, a bounded batch parameter evaluator
and an isolated trainer. Save BC/PPO losses and every episode to CSV, complete
optimizer/Torch RNG/model checkpoints after updates, input/source identities,
and pre/post deterministic training/validation GPU+CPU outcomes. Resume requires
matching identities and fresh output. Bound updates, population, optimizer epochs,
simulation count, stagnation, wall time and device memory. No policy selection
or early stopping may use held-out outcomes.

### 7. Consequences

Two references are a small integration fixture, not a reliability dataset.
Same-entry parallel episodes do not establish generalization. The native entry
failure remains in end-to-end evidence. Frozen entry geometry and privileged
simulation evaluation do not qualify camera-only grasp verification, hardware
control, generic transfers or the existing manipulation admission lease.

### 8. Verification

Test actor input allowlist, transformed log density, action bounds, failure reward
precedence, gradient updates and exact checkpoint/RNG restoration. Execute a
short BC/PPO batch pilot, retain failures and compare deterministic pre/post
policy on an excluded camera entry with canonical CPU replay.

### 9. Research relevance

This provides a measured shared-policy learning baseline over verified planner
parameters. It separates neural fitting, physical execution and independent
evaluation instead of inferring success from loss or reward alone.

### 10. Report-ready summary

ATOM's first accelerated learning pilot is a camera-feature-conditioned, shared
PPO macro policy over three physical planner parameters, initialized from CEM.
Its scope is isolated close/lift/hold from verified native entries, with canonical
CPU evaluation and no implied crowded-board or hardware capability.

### 11. References

- [PPO paper](https://arxiv.org/abs/1707.06347)
- [PyTorch distribution APIs](https://docs.pytorch.org/docs/stable/distributions.html)
- [S058: constrained CEM reference](S058-bounded-isolated-cem-grasp-pilot.md)
- [S060: actor/privileged demonstration boundary](S060-camera-command-demonstration-boundary.md)
