# S053 — Isolated native MJWarp research backend

**Status:** Accepted (design; acceleration and physics parity unverified)

**Date:** 2026-11-21

**Decision owners:** Robotics, simulation, ML infrastructure

**Related experiments:** EXP-0001, EXP-0002

**Related findings:** RF-0001, RF-0002

**Supersedes:** None

### 1. Context

The existing Windows pipeline uses MuJoCo 3.17.0, native ac:vision/ac:motion DLLs
and PyTorch/SB3. Repeated reach success does not resolve crowded insertion or
contact mechanics. A new request prioritizes batched GPU candidate experiments
and later shared-policy training without weakening the canonical CPU reference.

### 2. Evidence

The host reports RTX 5070 Ti, SM120, 16,303 MiB VRAM, driver 617.14, Windows 10
Pro build 19045 and Ryzen 5 3600X (6 cores/12 threads). The installed Torch build
is 2.14.1+cu130 and lists sm_120. Package resolution finds mujoco-warp 3.17.0
and warp-lang 1.19.0 Windows x86-64 wheels. Kernel execution and parity remain
separate experimental checks; device enumeration alone proves neither.

### 3. Decision

Keep MuJoCo 3.17.0 as the canonical reference. Install matching mujoco-warp
3.17.0 with pinned Warp dependencies in `simulation/mujoco/accelerated/.venv`.
Try native Windows first; evaluate WSL2 only if native GPU execution fails.
Retain the existing environment, drivers, assets, controllers and checkpoints.
Place optional backend code behind an interface that does not import Warp in
the ordinary CPU workflow. Use `accelerated/runs` for fresh local artifacts and
`docs/research` for experiment records and catalogs.

### 4. Alternatives considered

Upgrading the canonical environment to the latest MuJoCo would confound the
comparison. WSL2 would also require Linux native module builds. MJX/JAX adds a
second ML stack without a current differentiation requirement. Existing CPU
MuJoCo remains the fallback and verification reference.

### 5. Technical rationale

Matching simulator release numbers reduces one avoidable parity variable. Native
Windows preserves the current DLL integration. MJWarp batching can be assessed
independently of renderer and policy changes. Throughput remains a hypothesis
until measured under a defined workload.

### 6. Implementation

Add an isolated dependency lock, hardware/kernel probe, bounded batch smoke,
CPU/GPU parity checks and benchmark entry points. Begin with a contact fixture,
then import the unchanged robot/gripper model. No physics simplification or
backend switch is implicit in creating this environment.

### 7. Consequences

GPU float32 trajectories may differ from CPU float64. Mesh contact and equality
coupling require explicit qualification. CUDA graph compilation has startup
cost. Use small initial batches, explicit contact/constraint capacities, memory
headroom, wall-time limits and overflow rejection before expanding budgets.

### 8. Verification

EXP-0002 must execute an actual Warp CUDA kernel and minimal GPU contact physics.
Later parity must check initial state, actuation, contacts/forces and complete
grasp replay. No extensive CEM or RL run is admitted by this design ADR alone.

Post-decision verification: EXP-0002 passed an actual CUDA kernel and primitive
contact dynamics at 1/16 worlds. Six resource-request guard tests passed. These
checks establish native execution, not robot parity or acceleration.

### 9. Research relevance

Separate backend acceleration from control/geometry changes so manipulation
quality and useful experimentation throughput can be measured independently.

### 10. Report-ready summary

ATOM retains canonical CPU MuJoCo and introduces an isolated, version-matched
MJWarp research environment. Native Windows is evaluated first on the measured
SM120 workstation. Acceleration and manipulation parity require independent
experiments before GPU-generated trajectories can become training evidence.

### 11. References

- [MJWarp release 3.17.0](https://pypi.org/project/mujoco-warp/3.17.0/)
- [MJWarp repository](https://github.com/google-deepmind/mujoco_warp)
- [Warp 1.19 installation](https://nvidia.github.io/warp/v1.19/user_guide/installation.html)
- [Research index](../../../docs/research/RESEARCH_INDEX.md)
