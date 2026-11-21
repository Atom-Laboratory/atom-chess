# EXP-0005 — Fixed-control robot physics batching

Date: 2026-11-21. Decision: S056. Baseline: unchanged MuJoCo 3.17.0 isolated
full-gripper model and restored held-pawn snapshot. No RL, CEM, rendering or
camera processing was part of the timed workload.

## Protocol and source

RTX 5070 Ti, sm120, Windows 10, driver 617.14; Ryzen 5 3600X, six physical CPU
cores. CPU MuJoCo native Batch uses one/six threads. GPU uses MJWarp 3.17.0,
Warp 1.19.0 and an eight-step CUDA graph. Every repetition resets the same full
integration state; timing excludes reset/compilation. World counts 1–64 used
128 steps and three repetitions. Counts 128–1024 used 256 steps and five
repetitions. This difference is explicit; comparisons below are paired within
each batch, not a claim of invariant scaling with duration.

## Results

[EXPERIMENTAL-EVIDENCE] Medians of aggregate integration world-steps/s:

| Worlds | CPU six threads | GPU graph | Interpretation |
| --- | --- | --- | --- |
| 16 | 131,752 | 32,501 | CPU faster |
| 32 | 130,383 | 60,008 | CPU faster |
| 64 | 121,525 | 116,203 | Similar; measured CPU median slightly faster |
| 128 | 131,909 | 100,937 | CPU faster in this run |
| 256 | 134,298 | 192,316 | GPU approximately 1.43× CPU |
| 512 | 116,419 | 932,829 | GPU approximately 8.01× CPU |
| 1024 | 124,632 | 1,424,059 | GPU approximately 11.43× CPU |

The largest run observed 74.49 MiB in the Warp allocation pool, excluding driver,
compiler and other processes. This is not total dedicated VRAM usage. Final
per-repetition health checks were clear and finite; these historical benchmark
runs did not cumulatively OR transient overflow flags across every internal
step. Do not describe final samples as a continuous proof of no transient flag.
The full recorded-control parity experiment separately accumulates such flags.

Graph-captured physics gains are not training gains. CPU/GPU initializations and
host transfers have additional costs. All worlds here share the same restored
hold state and controls; different robot trajectories/contact distributions may
scale differently. Workstation graphics/application contention was not controlled.
At 128 worlds the GPU result was nonmonotonic; preserve it rather than smoothing.

## Artifacts and reproduction

[FIG-0003](../../../simulation/mujoco/accelerated/reports/EXP-0005/figures/FIG-0003-physics-throughput.svg)
plots medians and min–max raw repeats. SVG, PDF and PNG plus source hashes are
colocated. [Combined samples](../../../simulation/mujoco/accelerated/reports/EXP-0005/figures/combined-samples.csv)
retain the raw observations; original reports are preserved under `small`,
`large` and `1024` in that evidence directory. Each local run also retains source
snapshots, full states, request and stdout/stderr. CLI implementation was a
precommit diff over f90de4a; executed snapshot hashes define the exact workload.

Follow the [benchmark commands](../../../simulation/mujoco/accelerated/README.md).
No optimizer, policy inference, camera renderer, reset-heavy episode rate or
capture task throughput was measured. There is no preferred universal RL batch
size yet. Use a small qualified candidate pilot first, then choose batching from
the complete workload rather than GPU utilization alone.
