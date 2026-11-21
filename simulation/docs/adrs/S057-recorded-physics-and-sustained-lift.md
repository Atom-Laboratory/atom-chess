# S057 — Record complete physics transitions and verify a sustained lifted hold

**Status:** Accepted (experimental diagnostic and replay data)

**Date:** 2026-11-21

**Decision owners:** Manipulation verification, simulation datasets

**Related experiments:** EXP-0004

**Related findings:** RF-0001

**Supersedes:** None; historical short-lift results retain their original scope

### 1. Context

The isolated canonical pawn rose about 44.8 mm, but its prior success test did
not include a dedicated lifted-hold interval. Saved final snapshots also omitted
integration fields needed for exact CPU replay and GPU trajectory comparison.

### 2. Evidence

The current local supervisor already checks swept paths, tracking, contact loss,
topples, freshness and motion settling on every action. Those checks can guard
an unchanged hold command. MuJoCo `mjSTATE_INTEGRATION` includes hidden state
such as warmstarts and actuator history absent from qpos/qvel/ctrl snapshots.

### 3. Decision

Add opt-in per-physics-step recording before/after mj_step, after actual bounded
actuator controls have been set. Save complete integration states, phase labels,
model identity and numeric format in a compressed immutable run artifact. Never
use this privileged recording to generate actor inputs or movement targets.

Add an explicit lifted-hold duration. Issue the unchanged target through the
existing supervisor and require retained bilateral contacts, minimum measured
one-piece-height rise, settled feedback and no more than the declared slip
threshold for the entire interval. The initial pilot declares one simulated
second and 3 mm maximum vertical drop. These are experimental evaluation
criteria, not measured hardware specifications. A failure stays failed.

### 4. Alternatives considered

Reconstructing old warmstarts invents history. One final contact sample cannot
demonstrate sustained holding. A weld or reset would invalidate the physical
grasp test. Recording only applied targets cannot diagnose backend divergence.

### 5. Technical rationale

The recorder is a passive diagnostic observer. The ordinary controller is
unchanged when it is disabled. Complete recorded input transitions support
canonical exact replay, one-step GPU comparisons and open-loop outcome checks.

### 6. Implementation

An optional Simulation step observer records integration state at actual
physics boundaries. The native diagnostic CLI owns recording lifecycle and
saves partial evidence even on failure. A separate hold evaluator emits raw
rise, contact, settling and elapsed-time samples under the same safety checks.

### 7. Consequences

Recording adds host overhead and must be excluded from throughput comparisons.
Complete state and forces are privileged diagnostic data. Camera-only grasp
outcome verification, occupied-board entry and RL admission remain unqualified.
Large transition artifacts stay in ignored run storage; small summaries/hashes
are committed.

### 8. Verification

Replaying every recorded CPU transition from its complete input must match its
stored output before using the dataset for GPU comparison. Test recorder
noninterference and initial/final state handling. Test contact-loss/height/slip
failures independently of positive hold outcomes.

### 9. Research relevance

This separates successful contact, lifted movement and sustained holding while
producing reusable, traceable physical demonstrations and parity inputs.

### 10. Report-ready summary

ATOM records full canonical integration transitions without influencing control
and verifies a separately timed lifted hold using explicit physical criteria.
Historical short-lift successes are not relabeled as sustained-hold successes.

### 11. References

- [Simulation backend](../../mujoco/src/atom_mujoco/backend.py)
- [Native diagnostic](../../mujoco/examples/qualify_hybrid_approach/README.md)
- [Full-state parity boundary](S054-complete-state-cpu-gpu-parity-boundary.md)
