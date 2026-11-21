# S054 — Complete-state CPU/GPU parity boundary

**Status:** Accepted (design; robot parity pending)

**Date:** 2026-11-21

**Decision owners:** Simulation physics, GPU infrastructure, robotics verification

**Related experiments:** EXP-0003

**Related findings:** RF-0001, RF-0003

**Supersedes:** None

### 1. Context

EXP-0002 establishes native CUDA execution on a primitive contact fixture. It
does not qualify the robot's mesh hulls, coupled fingers, actuator gains or
elliptic contact forces. Historical saved qpos/qvel/ctrl snapshots omit solver
warmstarts and cannot reproduce the exact old integration state.

### 2. Evidence

The read-only asset audit found 66 gripper hulls, including 44 with more than
64 vertices, and a free pawn with no weld. The model also uses an equality
coupling and independent planner self-collision checks absent from engine masks.
The Robotics parity guide recommends complete integration-state synchronization,
stage-ordered comparisons, contact matching independent of buffer order and
float32 conditioning rather than a single long-trajectory equality assertion.

### 3. Decision

Introduce independently testable CPU and Warp batch adapters sharing full
`mjSTATE_INTEGRATION` reset/state contracts, explicit controls and selected-world
reset masks. Keep Warp optional in the CPU path. Copy verified models without
geometry, solver, actuator or mask changes. Enforce finite world/memory/time and
contact/constraint budgets, and report all overflow/convergence flags.

Begin robot parity with parked and restored grasp snapshots. Initialize omitted
snapshot fields to the same explicit defaults in both engines; label these as
new comparison states, not exact historical force reconstruction. Compare
kinematics, actuation and dynamics in pipeline order, then contact counts and
forces by canonical geom pair. Record raw and normalized errors and any ambiguous
grazing contacts. Follow with single-step comparisons and complete recorded
canonical trajectories before CEM qualification.

### 4. Alternatives considered

Copying qpos/qvel alone leaves hidden state mismatched. Contact-index equality
is invalid under GPU ordering. Matching only a final lift label can conceal
incorrect contact forces. Simplifying meshes or changing friction would confound
the backend comparison and requires separate evidence.

### 5. Technical rationale

Separate numerical precision, state synchronization, collider behavior and
controller semantics. Use the parity guide's initial dimensional tolerances:
kinematics 1e-5 absolute/1e-4 relative; actuator forces 1e-3/1e-3 with explicit
float32 affine-rounding bounds; constraint dynamics 1e-1/1e-2 as a diagnostic
screen. Contact forces additionally need a task-scale comparison. These are
diagnostic thresholds, not hardware clearance or manipulation acceptance limits.

### 6. Implementation

Add optional batch adapters, state/reset isolation tests, a bounded robot parity
entry point and experiment artifacts under `accelerated/runs/EXP-0003`. Keep
source/model/version fingerprints with each run. Rendering and actor observations
remain separate from privileged parity measurements.

### 7. Consequences

Host copies are acceptable for qualification but cannot represent optimized
training throughput. Float32 grazing/convex-contact changes may need a CPU
rounded-state baseline. Buffer or material outcome failures block advancement;
they are not removed by raising tolerances after seeing the result.

### 8. Verification

Test exact CPU selected-world reset isolation and complete state restoration.
On CUDA, check actual allocation limits, overflow flags and synchronized forward
states before open-loop stepping. A primitive pass never substitutes for robot
contact, lift or full-trajectory validation.

### 9. Research relevance

This defines which accelerated samples can later count as physical manipulation
evidence and separates backend performance from policy quality.

### 10. Report-ready summary

ATOM compares canonical CPU MuJoCo and version-matched MJWarp through a complete
state/controls interface. Initial robot tests diagnose stage-specific differences
and contact behavior without changing the physical model. Large optimization
or training budgets remain gated by relevant outcome parity.

### 11. References

- [Robotics parity skill](C:/Users/maria/.gemini/config/plugins/robotics/skills/parity/SKILL.md)
- [MJWarp documentation](https://mujoco.readthedocs.io/en/3.17.0/mjwarp/)
- [CPU baseline](../../../docs/research/experiments/EXP-0001-canonical-baseline.md)
- [GPU execution](../../../docs/research/experiments/EXP-0002-native-gpu-environment.md)
