# S056 — Matched, bounded robot contact physics benchmarks

**Status:** Accepted (protocol; operating batch size not yet selected)

**Date:** 2026-11-21

**Decision owners:** GPU infrastructure, simulation benchmarking

**Related experiments:** EXP-0005

**Related findings:** RF-0003

**Supersedes:** None

### 1. Context

The primitive GPU smoke was slower at one world, and its CPU timing varied.
Those timings do not select a useful batch size for the unchanged robot model.
The initial two-state robot forward/step screen passed, enabling a limited
physics benchmark without admitting long-horizon manipulation learning.

### 2. Evidence

The robot has 66 full-gripper hulls and a contact-rich held-pawn snapshot.
CPU MuJoCo 3.17 offers a complete-integration-state batch API with a thread pool.
Warp supports graph capture. Camera, native planning and policy work were the
dominant overheads in the old single-environment training pipeline.

### 3. Decision

Compare the same defined held-pawn state and fixed actuator controls on CPU
one-thread batch, CPU up-to-six-thread batch and GPU graph-captured batch. Use
complete integration state, identical time step and model, warmup, three or more
timed repetitions and fresh reset before every repetition. Measure reset costs
separately. Increase world counts progressively within explicit memory, world,
physics-step and process-time budgets. Reject nonfinite states, capacity flags
or numerical warnings; preserve failures. Save raw repeat samples and health.

### 4. Alternatives considered

Comparing only optimizer times or GPU utilization does not measure useful
simulation throughput. A serial Python CPU loop would bias the comparison
against available native threading. Rendering every world changes the workload
and is excluded from these physics timings.

### 5. Technical rationale

Both engines perform the same number of physical integration steps without
policy updates or camera rendering. GPU compilation, host copies and resets are
reported outside the physics-only region. CPU batch `nstep` also avoids Python
per-step overhead. Record host/GPU contention context; small samples do not
establish universal hardware performance.

### 6. Implementation

Add a bounded benchmark entry point using the full-state adapter, native CPU
Batch and Warp graph replay. Local raw JSON/CSV belong to fresh EXP-0005 runs.
The experiment report must distinguish aggregate world-steps/s from episodes/s
and full training throughput, which this workload does not measure.

### 7. Consequences

Repeated identical hold states are a controlled benchmark, not independently
randomized manipulation tasks. A faster physics batch may still be dominated by
vision/planning in end-to-end training. No collision masks, meshes or solver
iterations are changed for timing.

### 8. Verification

Test resource bounds before allocation. Verify CPU batch integration-state
loading and final states. Check GPU overflow and finite state for each timed
repetition. Compare lift/hold outcome in the independent replay experiment;
throughput alone never qualifies grasp success.

### 9. Research relevance

This produces defensible hardware-specific performance evidence for later CEM
and rollout batching without confusing acceleration with manipulation quality.

### 10. Report-ready summary

ATOM benchmarks unchanged robot physics under identical fixed-control contact
conditions, with matched resets and repeated measurements on serial CPU,
threaded CPU and graph-captured GPU batches. Compilation and reset overheads
remain separate, and no end-to-end training acceleration is inferred.

### 11. References

- [CPU batch implementation](https://github.com/google-deepmind/mujoco/blob/main/python/mujoco/batch.py)
- [MJWarp graph capture](https://mujoco.readthedocs.io/en/3.17.0/mjwarp/)
- [EXP-0003](../../../docs/research/experiments/EXP-0003-robot-physics-parity.md)
