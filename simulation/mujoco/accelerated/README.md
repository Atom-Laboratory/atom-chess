# GPU simulation research

This module evaluates MuJoCo Warp separately from the existing canonical CPU
training environment. Begin with [the research index](../../../docs/research/RESEARCH_INDEX.md)
and [progress](../../../docs/research/RESEARCH_PROGRESS.md). GPU execution,
robot-model parity and speedup are separate qualification gates. No GPU-trained
manipulation policy is currently qualified.

## Isolated native Windows environment

Use PowerShell from the repository root. Keep the existing
`simulation/mujoco/.venv` unchanged. The initial stack deliberately matches the
canonical MuJoCo 3.17.0 release rather than upgrading the reference physics.

```powershell
uv venv --python .\simulation\mujoco\.venv\Scripts\python.exe simulation/mujoco/accelerated/.venv
uv pip sync --python simulation/mujoco/accelerated/.venv/Scripts/python.exe simulation/mujoco/accelerated/requirements-windows-py312.lock
uv pip install --python simulation/mujoco/accelerated/.venv/Scripts/python.exe --no-deps -e simulation/mujoco
$gpuPy = '.\simulation\mujoco\accelerated\.venv\Scripts\python.exe'
```

## CUDA/contact smoke

```powershell
& $gpuPy -u -B simulation/mujoco/accelerated/probe.py --worlds 1 --steps 500
& $gpuPy -u -B simulation/mujoco/accelerated/probe.py --worlds 16 --steps 500
& $gpuPy -B -m pytest simulation/mujoco/accelerated/tests -q
```

The parent creates a fresh output directory, snapshots executed source and lock,
and bounds its worker with `--max-wall-s` (default 180 s, including imports/JIT).
The worker runs an actual CUDA array kernel, then canonical CPU and GPU sphere
contact dynamics with identical initial state and controls. It rejects nonfinite
state, any overflow/iteration flag or final qpos difference above 0.1 mm in this
primitive fixture. This threshold does **not** qualify the robot's contacts or
grasp behavior.

`--max-gpu-mib` defaults to 2048. The probe requires that budget plus 1 GiB free
device headroom and checks Warp's current/peak allocation pool. This is a
monitored allocation budget, not an operating-system quota; driver/compiler
allocations and other graphics applications are outside the Warp pool. No
system display driver or CUDA toolkit replacement is performed.

`report.json`, `request.json`, source snapshots and stdout/stderr are colocated
in fresh `accelerated/runs/EXP-0002/RUN-*` directories. Cold JIT startup and
physics execution are separate metrics. The CPU timing is one reference world,
not a matched multiworld throughput benchmark. Rendering, planning, policy
updates, episodes and resets are absent. A one-world smoke cannot establish
speedup. See the research experiment record for actual measurements.

See [ADR S053](../../docs/adrs/S053-isolated-native-mjwarp-research-backend.md).

## Robot forward and single-step parity

Set `$config` to a prepared robot `environment.json`. Optionally set `$snapshot`
to an existing diagnostic `state-final.json`; omitted hidden state is explicitly
initialized identically, so this does not reconstruct historical contact forces.

```powershell
& $gpuPy -u -B simulation/mujoco/accelerated/parity.py --config $config `
  --snapshot $snapshot --max-wall-s 600 --max-gpu-mib 2048
& $gpuPy -B -m pytest simulation/mujoco/accelerated/tests -q
```

The fresh EXP-0003 output contains complete comparison integration states,
stage-specific raw/normalized errors, order-independent contact pair forces,
single-step error, selected reset isolation, allocation and overflow status.
The CLI returns a failure status when the screen does not pass. Forward and
single-step agreement is a limited diagnostic screen; complete contact-rich
rollout/hold parity is a separate gate. No camera images or simulator truth from
this qualification enter a deployable actor. See
[S054](../../docs/adrs/S054-complete-state-cpu-gpu-parity-boundary.md).

## Matched physics benchmark

```powershell
& $gpuPy -u -B simulation/mujoco/accelerated/benchmark.py --config $config `
  --snapshot $snapshot --worlds 1 16 32 64 --max-worlds 64 `
  --steps 128 --repeats 3 --threads 6 --max-gpu-mib 2048 --max-wall-s 900
```

Use the same verified held-pawn snapshot for CPU and GPU. This compares native
CPU batches with one/six threads against graph-captured GPU physics. Full resets,
warmup, compilation and three or more raw repetitions are separate. The process
is bounded; fresh EXP-0005 outputs contain `samples.csv`, summaries, final states,
health and source snapshots. Failed capacity/numerical checks stop the run.

This workload excludes camera, planning, policy inference/optimization and
rendering. It measures world-steps/s, **not** episodes/s or full RL speedup.
Identical initial states do not test randomized-world generalization. Expand
batch size only after observing memory and stability. See
[S056](../../docs/adrs/S056-matched-robot-physics-benchmark.md).

To regenerate scientific figures from retained benchmark run directories, use
the canonical Python environment with its diagnostics/Matplotlib extra:

```powershell
& .\simulation\mujoco\.venv\Scripts\python.exe -B simulation/mujoco/accelerated/plot_benchmarks.py `
  --runs $smallRun $largeRun $largestRun --output $freshFigureDirectory
```

The three input variables are completed EXP-0005 run directories, each containing
`report.json` and `samples.csv`. The output must not already exist. It contains
combined unsmoothed CSV, figure-source hashes and FIG-0003 in SVG/PDF/PNG. The
figure identifies different durations/repeat counts and min–max variability.

## Recorded canonical grasp replay

```powershell
# Record a native diagnostic using --lift-hold-s 1 --record-physics first.
$transitions = Join-Path $canonicalRun 'physics-transitions.npz'
& $gpuPy -u -B simulation/mujoco/accelerated/replay.py --config $config `
  --transitions $transitions --worlds 1 --max-wall-s 600
& $gpuPy -u -B simulation/mujoco/accelerated/replay.py --config $config `
  --transitions $transitions --worlds 16 --max-wall-s 300
$env:ATOM_TEST_CUDA = '1'
& $gpuPy -B -m pytest simulation/mujoco/accelerated/tests -q
```

Recording must match the verified model/hash and complete state signature.
Independent CPU steps and continuous CPU tape replay are checked before GPU
rollout. GPU metrics accumulate overflow/convergence flags at every step and
record states, pad contacts and forbidden engine contacts. Reports preserve
dimensional limits, hold/slip/settling/upright metrics and experiment scope.
The parent bounds wall time and snapshots executed source.

The GPU follows recorded canonical controls; this is not autonomous camera
perception or policy inference. Identical worlds are not independent trials.
Robot self pairs checked by the planner remain separate from engine masks.
Fresh outputs include GPU trajectory NPZ, reports, source copies and failure logs.
