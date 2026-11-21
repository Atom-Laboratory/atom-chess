# EXP-0002 — Native Windows SM120 GPU environment qualification

Date: 2026-11-21. Related ADR: S053. Status: native CUDA/contact smoke passed.

## Question and hypothesis

Can a version-matched MJWarp stack execute CUDA physics on this workstation
without replacing the canonical Windows development environment? Enumeration
and package availability are prerequisites; an actual GPU kernel and contact
smoke test must decide the execution result.

## Observed environment

- GPU: RTX 5070 Ti, compute capability 12.0, 16,303 MiB VRAM, driver 617.14.
- OS: Windows 10 Pro 10.0.19045.
- CPU: AMD Ryzen 5 3600X, 6 cores/12 logical processors.
- RAM: 33,501,512 KiB visible; free memory varies with other workstation apps.
- Existing Python: 3.12.14; MuJoCo 3.17.0; Torch 2.14.1+cu130; SB3 2.9.2.
- Existing Torch reports CUDA available and sm_120 among its compiled targets.
- Native package resolution: mujoco-warp 3.17.0 requires warp-lang >=1.15;
  version 1.19.0 supplies a Windows x86-64 wheel. No system nvcc was found on PATH.

These hardware observations alone establish neither kernel compatibility nor speedup.

## Bounded protocol

Create a fresh isolated environment, pin matching MuJoCo/MJWarp 3.17.0 and Warp
1.19.0, execute a CUDA array kernel, then a small batched contact fixture. Begin
with one world and bounded steps. Record actual versions, device, elapsed time,
memory, warnings and buffer capacities. Reject overflow or nonfinite states.
Only after this smoke proceeds, assess the unchanged robot and contact parity.

## Results, limitations and artifacts

[VERIFIED-RESULT] The actual CUDA array kernel and 500-step primitive contact
smoke passed with one and sixteen worlds. Both final qpos comparisons had maximum
absolute error 5.344e-9 against the single CPU reference. No overflow/iteration
flags were observed at the final check. MuJoCo/MJWarp 3.17.0, Warp 1.19.0 and
bundled CUDA 13.4 executed natively on sm120. No WSL or display-driver change.

| Run | Worlds | Physics steps/world | GPU physics wall | First GPU step/JIT | Warp pool high watermark |
| --- | --- | --- | --- | --- | --- |
| Native cold smoke | 1 | 500 | 0.171439 s | 61.005973 s | 55,104 bytes |
| Cached batch smoke | 16 | 500 | 0.157783 s | 1.333828 s | 711,909 bytes |

These are **smoke timings**, not a matched throughput benchmark. Their single
CPU reference timings varied (0.033747 s and 0.004259 s), so a speedup estimate
would be unjustified. The one-world GPU execution was slower than its CPU
reference. Rendering, resets, robot geometry, planning, policy updates and
episode throughput were not measured. Worlds began with identical states;
independent reset/isolation tests remain pending.

Raw reports: [world 1](../../../simulation/mujoco/accelerated/reports/EXP-0002/native-world1.json)
and [world 16](../../../simulation/mujoco/accelerated/reports/EXP-0002/native-world16.json).
The first report's historical `peak_nacon` field is the final contact count,
not a sampled maximum; `total_worker_wall_s` excludes module import time. The
later implementation names those quantities correctly and records process wall
time. Original reports and executed source snapshots were preserved.

Reproduce with the [GPU module README](../../../simulation/mujoco/accelerated/README.md).
The parent enforces 180 s process time and a declared 2,048 MiB Warp pool budget
plus free-device headroom. Pool accounting excludes driver/compiler and other
process allocations. Existing workstation applications may contend for memory
and GPU time. No robot-contact parity, general reproducibility guarantee or
training acceleration is inferred from this primitive test.
