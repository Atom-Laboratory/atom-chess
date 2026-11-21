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

## Isolated Stage A CEM pilot

`cem.py` optimizes three command parameters: closing-load factor, fraction of
compiled finger closing speed, and fraction of the existing local vertical
rate. Each member includes close, settle, lift and one-second hold from an
executed near-grasp entry. Source XY is frozen from the camera-derived native
diagnostic. Friction, mass, gain, geometry and camera are not optimized.

Prerequisites: a verified isolated elliptic/10 fixture and a successful canonical
recorded hold run containing `local-report.json`, `physics-transitions.npz` and
its JSON hash sidecar. The config must match that recording. Example for the
retained local fixture, from the repository root:

```powershell
$gpuPy = '.\simulation\mujoco\accelerated\.venv\Scripts\python.exe'
$config = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/solver-comparison-daeb5509116a43e5a1f770f39e44367d/elliptic10/environment.json'
$reference = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/canonical-recorded-hold-73d79eb2045643e3a3f9851c7cf6ca19'
& $gpuPy -u -B simulation/mujoco/accelerated/cem.py --config $config --reference $reference `
  --population 8 --generations 2 --max-simulations 16 --max-duration-s 40 `
  --max-wall-s 300 --max-gpu-mib 2048 --seed 970300
& $gpuPy -B -m pytest simulation/mujoco/accelerated/tests/test_cem.py -q
```

Complete nominal closure/carried-lift sweeps and compiled limits filter
candidates before GPU simulation. Physical validity and held-lift success rank
ahead of height/time. A best GPU result is independently replayed on canonical
CPU; a scalar score cannot declare success. Invalid paths, failed grasps and
budget/dependency errors remain recorded. The original 1 mm margin remains for
all pairs except the explicit selected-piece/moving-finger near-contact margin.

Fresh EXP-0006 outputs contain generation JSON, raw candidate CSV, distribution
and RNG checkpoints, accepted control tapes, best candidate NPZ, CPU result and
source snapshots. `--resume <checkpoint-N.json>` continues a matching verified
distribution in a fresh output, not a physics process or a neural policy.

This pilot does not render every world or train RL. The native diagnostic Watch
remains the visual reference. It does not optimize approach/wrist/height yet,
randomize task starts, solve occupied-board entry or qualify a camera-only
outcome verifier. Identical initial states are not generalization evidence. See
[S058](../../docs/adrs/S058-bounded-isolated-cem-grasp-pilot.md).

To test frozen winning parameters on a new camera-localized, physically captured
reference, generate another recorded canonical hold with a different seed, then:

```powershell
& $gpuPy -u -B simulation/mujoco/accelerated/evaluate_candidate.py --config $config `
  --reference $newReferenceRun --winner (Join-Path $cemRun 'report.json') --max-wall-s 180
```

`$newReferenceRun` is a distinct successful recorded native diagnostic;
`$cemRun` is a completed CEM run with canonical winner verification. This command
does not optimize again. It transfers three command parameters and derives XY
from the new signed camera reference. Its fresh output stores GPU/CPU outcomes,
input hashes and the complete candidate NPZ. Passing one new entry is a small
held-out test, not a reliability or crowded-operation claim. Current checkpoint
identity also binds the exact reference report/handoff; earlier prototype
checkpoints without those fields require their preserved executed source or a
fresh search, rather than silently continuing with different input evidence.

## Verified camera/command demonstrations and Watch

Use the **canonical** environment for RGB export and native Watch; it already
contains Pillow. `$config`, `$reference` and `$candidate` must be matching,
successful EXP-0006 inputs, not arbitrary model bundles. Run from the repository
root. This retained example exports the additional isolated entry:

```powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$config = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/solver-comparison-daeb5509116a43e5a1f770f39e44367d/elliptic10/environment.json'
$reference = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/canonical-reference-970201-headless-ad248b4d06c54f79a2147914ba221661'
$candidate = 'simulation/mujoco/accelerated/runs/EXP-0006/RUN-heldout-frozen-970201-744ed6f8acaf40ae8043933750e74540'
& $py -u -B simulation/mujoco/accelerated/demonstrations.py `
  --config $config --reference $reference --candidate $candidate
& $py -B -m pytest simulation/mujoco/accelerated/tests/test_demonstrations.py -q
```

The default opens a **separate process** with two finite physical replay cycles
after export. Its overlay says **REPLAY — NOT RL TRAINING**. `--headless` exports
without Watch. `--watch-repeats 4 --watch-speed 1` requests four real-time cycles;
display speed never changes physics timestep. Each subprocess has a wall budget.
Do not open Watch after destroying an offscreen renderer in the same process:
the initial combined attempt crashed natively on this Windows host after export.

`--stride 50` means one RGB/action chunk per 50 physics steps (0.1 s in this
fixture), **not** 50 environments or episodes. `--max-frames 512` and
`--image-size 96` bound output; RGB is rendered with the original camera then
resized. Three full-resolution images are retained. Fresh EXP-0007 outputs contain:

| Artifact | Content and boundary |
| --- | --- |
| `actor.npz` | Pre-action RGB, previously issued actuator command, signed camera source XY, source/target task and planned phase; no measured state/contact |
| `actions.npz` | Exact subsequent actuator command chunks, `start_step`, `valid_steps`; ignore padded tail commands |
| `privileged.npz` | Initial complete state, full command tape, pre-frame integration states, actual trajectory and contact/safety outcomes; excluded from actor input |
| `frame-metrics.csv` | Frame/step/phase, post-interval rise and contacts for analysis |
| `report.json` | Physical success, exact CPU replay comparison, source/model/reference/camera identities and artifact hashes |
| `watch/` | Default separate-process Watch log and report; presentation failures do not rewrite the export's physical outcome |

To replay a completed export without re-rendering the dataset, use its **full
fresh-run directory** from the exporter output:

```powershell
$demo = 'simulation/mujoco/accelerated/runs/EXP-0007/RUN-demonstration-970200-6b62b8d8e83d49c28d94ff6b6f713456'
& $py -u -B simulation/mujoco/accelerated/watch_demonstration.py `
  --config $config --demonstration $demo --repeats 4 --speed 1 --max-wall-s 180
```

Watch starts from the complete recorded near-grasp state and executes every
command with `mj_step`; it does not attach or reposition the piece during the
motion. It exits after the finite replay or when the user closes the window.
An export is accepted only after matching CPU re-execution and unchanged physical
criteria. The current dataset has two isolated entries; frames are correlated.
Split future training/test data by reference/run. The configured camera can be
occluded by the robot; these images alone do not establish a visual grasp verifier.
No BC/RL accuracy, crowded-board success or hardware readiness follows from export.
See [S060](../../docs/adrs/S060-camera-command-demonstration-boundary.md).

## Shared Stage A BC/PPO parameter-policy pilot

This experimental learner uses **ac:vision-derived features**, not raw RGB or
measured object/joint positions. One shared PyTorch MLP actor/critic selects the
same three parameters as CEM; native ac:motion generates and screens the resulting
trajectory. Each independent GPU world executes one complete close/lift/hold
macro action. It is a contextual bandit (gamma=0), not sequential visual servoing.
The existing reach/temporal camera PPO launchers remain separate.

Use the canonical Python for PyTorch and the isolated GPU Python for physics.
No Torch install or driver change is needed in the GPU environment. The following
complete block uses retained local verified fixtures; these ignored run archives
must exist. A fresh clone must first reproduce the reference/CEM/export steps
above. Run from the repository root:

```powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$gpuPy = '.\simulation\mujoco\accelerated\.venv\Scripts\python.exe'
$config = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/solver-comparison-daeb5509116a43e5a1f770f39e44367d/elliptic10/environment.json'
$trainReference = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/canonical-recorded-hold-73d79eb2045643e3a3f9851c7cf6ca19'
$validationReference = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/canonical-reference-970201-headless-ad248b4d06c54f79a2147914ba221661'
$trainDemo = 'simulation/mujoco/accelerated/runs/EXP-0007/RUN-demonstration-970200-6b62b8d8e83d49c28d94ff6b6f713456'
$validationDemo = 'simulation/mujoco/accelerated/runs/EXP-0007/RUN-demonstration-970201-headless-303fa156cbfb4b008bb0c9a1b033f3a7'
$expert = 'simulation/mujoco/accelerated/runs/EXP-0006/RUN-cem-bound-reference-9a4e243004dd43359c6d5c4db64c6898/report.json'
& $py -u -B simulation/mujoco/accelerated/train_parameters.py `
  --config $config --training-reference $trainReference --validation-reference $validationReference `
  --training-demo $trainDemo --validation-demo $validationDemo --expert $expert `
  --gpu-python $gpuPy --updates 3 --population 8 --max-wall-s 600
& $py -B -m pytest simulation/mujoco/accelerated/tests/test_parameter_policy.py -q
```

`--population 8` means eight independent physics worlds sampling **one shared
policy**, not eight networks. `--updates 3` bounds training to 24 complete macro
episodes, plus four deterministic pre/post evaluation episodes. `--bc-epochs 100`
fits the actor mean to the verified expert before PPO; `--ppo-epochs 4` caps gradient
passes over each batch. `--stagnation-updates 3` uses training reward only.
Neither optimizer epochs nor macro episodes are low-level physics steps.

The small network defaults to CPU (`--device cuda` is available); batched physics
runs on CUDA regardless. This initial process/host boundary deliberately preserves
the environments and is included in wall time. It is not an end-to-end GPU-resident
training-speed claim. Each batch also has `--batch-wall-s` and `--max-gpu-mib` budgets.

After a successful final training-reference action, the default exports its
demonstration and opens a bounded separate Watch replay. Its overlay identifies
**replay**, rather than live optimizer sampling. `--headless` suppresses that
presentation. Unsafe/rejected final actions are reported instead of replayed as
successful. This does not render every parallel environment.

Fresh EXP-0008 runs retain `bc-metrics.csv`, `training-metrics.csv`, `episodes.csv`,
every batch's action requests/geometric failures/physics NPZ and reports, exact
source snapshots, and `checkpoint-N.pt`/`policy.pt` with model, Adam and Torch RNG.
`before/` and `after/` contain separate GPU/CPU physical outcomes for training and
excluded validation references. Validation never controls gradients or stopping.
To continue, repeat the same full block with `--resume <prior-run>/policy.pt` and
a fresh output; identity checks bind inputs, schema, source and device. Continuation
restores optimizer/RNG but starts fresh independent physics episodes.

The actor sees 12 features: camera source XY, six issued entry actuator commands,
and four encoded source/target square coordinates. It is a 64/64 Tanh MLP, not a
CNN. Three tanh-Gaussian action outputs select load, closure-rate and lift-rate.
The critic predicts immediate macro reward. Failed geometry, forbidden contacts
or failed held lifts receive -100; success receives 10 minus duration/slip costs.
PPO uses clipped likelihood ratios, value loss and explicitly labeled base-Gaussian
entropy. Loss reduction never substitutes for the physical success checks.

Only one training reference and one excluded validation reference are currently
available in this recipe. This tests integration and shared updates, not learned
generalization or a reliability rate. Camera geometry is frozen at entry. Arbitrary
approach/height/wrist discovery, crowded entry, online visual success verification,
transfer/placement and hardware calibration remain open. See
[S061](../../docs/adrs/S061-shared-parameter-policy-stage-a.md).

Frozen-policy evaluation on another **successfully camera-localized recorded
native entry**, without BC or PPO updates:

```powershell
$policy = 'simulation/mujoco/accelerated/reports/EXP-0008/policy-update-4.pt'
$newReference = 'simulation/mujoco/examples/qualify_hybrid_approach/runs/canonical-reference-970202-efbc93c959ff41d2b7a4659920b3307f'
& $py -u -B simulation/mujoco/accelerated/evaluate_policy.py `
  --config $config --checkpoint $policy --references $newReference --gpu-python $gpuPy --max-wall-s 180
```

This adapter reads camera XY from the signed native reference and **only the
issued control command** from its command-history recording. It never queries
measured joint/object coordinates for actor inference; a regression test changes
all actual qpos/qvel while requiring identical actor context. The same command
history can be logged by a hardware controller. Physical state initializes the
evaluation world separately. Fresh outputs contain `inference.json`, exact
parameter requests and GPU/CPU outcome reports. `--references` accepts up to
sixteen declared entries. A recorded successful entry is a conditional starting
fixture, not proof that the policy can independently approach or acquire it.

Regenerate unsmoothed training figures with canonical Python/Matplotlib:

```powershell
$pilotRun = 'simulation/mujoco/accelerated/runs/EXP-0008/RUN-shared-parameter-pilot-997924736f9a4b7b89f699d265629d24'
$resumeRun = 'simulation/mujoco/accelerated/runs/EXP-0008/RUN-shared-parameter-resume-2644d927be2b4f83936aee61708f8862'
$figureOutput = Join-Path 'simulation/mujoco/accelerated/runs/EXP-0008' ('RUN-figure-' + [guid]::NewGuid().ToString('N'))
& $py -B simulation/mujoco/accelerated/plot_parameters.py --runs $pilotRun $resumeRun --output $figureOutput
```

The fresh folder contains FIG-0004 in SVG/PDF/PNG plus source hashes. Curves use
raw BC/PPO/episode CSV and CPU evaluation reports; no smoothing, confidence
interval or independent-reliability inference is added to this tiny pilot.
