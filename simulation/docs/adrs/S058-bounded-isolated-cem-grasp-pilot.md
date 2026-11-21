# S058 — Bounded isolated CEM for closure and lift commands

**Status:** Accepted (experimental Stage A pilot; no RL admission)

**Date:** 2026-11-21

**Decision owners:** Manipulation optimization, physics verification, ML research

**Related experiments:** EXP-0006

**Related findings:** RF-0001, RF-0003

**Supersedes:** None

### 1. Context

The corrected canonical controller executes an isolated lifted hold, and its
recorded controls reproduce that outcome in 1/16 GPU worlds. New candidates
still need independent path and physics checks. The occupied-board insertion
problem remains unresolved and must not be hidden by isolated optimization.

### 2. Evidence

EXP-0004 provides a physically executed pregrasp entry and complete states.
EXP-0005 measures batched physics potential, but not candidate-generation or
vision throughput. Existing slip/closure failures show that command timing and
preload are meaningful variables without changing model friction or gains.

### 3. Decision

Begin CEM with three bounded parameters: model-derived closing-load factor,
closing speed as a fraction of compiled finger speed, and lift speed as a
fraction of the existing static local rate. Keep the camera-derived source XY,
compiled grasp height, wrist, robot geometry and destination rise from the
verified reference. A candidate is a complete Stage A close, settle, lift and
one-second hold plan from the physically executed near-grasp entry. This is
not a full park-to-transfer candidate or occupied-board solution.

Generate quintic joint paths with compiled speed/force/travel bounds and the
command-derived static gravity term. Before simulation, screen the complete
closure and carried-object lift with the same collision pairs and explicitly
declared selected-finger near-contact margin. Simulator state may initialize
worlds or evaluate safety/outcomes; it must not supply movement target XY.

Simulate only geometrically accepted candidates in independent GPU worlds.
Rank lexicographically: validity/prohibited contact first, then measured held
lift success, then lift/hold quality and duration. A high scalar reward cannot
override a physical failure. Update a bounded diagonal Gaussian from elites;
retain the current best candidate. Bound populations, generations, duration,
total simulations, process wall time and memory. Checkpoint distribution/RNG
and all candidate failures; use fresh outputs for continuation.

### 4. Alternatives considered

Random/grid search remains a baseline. CMA-ES is deferred until evidence shows
that covariance adaptation helps this small pilot. Changing gains/friction or
collider geometry would confound command optimization. Simulating a failed
geometric candidate is unnecessary and can conceal planning failure.

### 5. Technical rationale

A small command-space pilot tests population evaluation, constraints and
scientific bookkeeping before adding wrist/height/waypoint dimensions. No
neural network is replaced; this is trajectory optimization before learning.

### 6. Implementation

Add pure CEM sampling/ranking logic, bounded command-tape generation, GPU tape
evaluation, per-candidate outcome records, generation CSV/checkpoints and a
canonical CPU replay of the best GPU candidate. Save every parameter bound,
model/source/input hash and seed. Search uses the existing native IK.

### 7. Consequences

The fixed near-entry distribution does not establish generalization. GPU
results alone cannot qualify the winner: canonical CPU replay must pass. Vision
is not rendered for every environment every frame; targets are frozen from the
verified camera reference. Real-time camera correction and policy training are
later stages. Larger physics batch throughput does not justify large initial
search budgets.

### 8. Verification

Test bounded sampling, deterministic RNG restoration and lexicographic physical
failure precedence. Run a short population pilot, retain negative candidates,
and verify its best trajectory on canonical CPU with unchanged physical criteria.
Do not admit manipulation RL merely because CEM returns a candidate.

### 9. Research relevance

This measures whether command-space search can find useful physical grasps more
efficiently while preserving the distinction between geometry, contact, lift,
holding, generalization and learned control.

### 10. Report-ready summary

ATOM evaluates a bounded three-parameter isolated close/lift CEM pilot from a
verified camera-localized entry. Complete candidate paths are screened before
GPU physics; physical outcome hierarchy and canonical CPU winner replay govern
acceptance. Occupied-board operation and RL generalization remain separate gates.

### 11. References

- [Canonical/GPU held lift](../../../docs/research/experiments/EXP-0004-canonical-held-lift-and-gpu-replay.md)
- [Benchmark](../../../docs/research/experiments/EXP-0005-physics-batching-benchmark.md)
- [Recorded physics](S057-recorded-physics-and-sustained-lift.md)
