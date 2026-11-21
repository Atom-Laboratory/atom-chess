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
