# Reproducing ATOM Chess training

Use the Windows x64 workflow below from the repository root. The canonical
experiment checks isolated local reach through the real perception and native
motion pipeline. It collects a short PPO update and compares the same two
held-out seeds before and after training. Treat this as a reproducibility
check. The diagnostic report tracks the separate question of learning.

## Install and build

Clone the repository and check out the branch containing this guide. The
canonical fixture uses tracked URDF, mesh, gripper and ArUco assets. No
submodule or previous run directory is required.

```powershell
git clone https://github.com/Atom-Laboratory/atom-chess.git
Set-Location atom-chess
git switch codex/atom-rl-training-diagnostics
py -3.12 -m venv simulation/mujoco/.venv
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $py -m pip install -r simulation/mujoco/requirements-windows-py312.lock -e 'simulation/mujoco[test,rl,diagnostics]'
& $py -m pip check
```

Use CMake, MSVC x64 with C++ desktop tools and an OpenCV 4.12 installation
with ArUco. Set `OpenCV_DIR` to the directory containing OpenCVConfig.cmake.
The example uses the tested Visual Studio 18 2026 generator. CMake copies the
OpenCV runtime into the Release output on the tested installation.

```powershell
$opencv = Read-Host 'Directory containing OpenCVConfig.cmake'
cmake -S . -B build/rl-native -G 'Visual Studio 18 2026' -A x64 "-DOpenCV_DIR=$opencv" -DBUILD_TESTING=OFF -DACCHESS_BUILD_VIEWER=OFF -DACVISION_NATIVE_RUNTIME=ON -DACMOTION_NATIVE_RUNTIME=ON
cmake --build build/rl-native --config Release --target motion_runtime acvision_runtime perception_image
```

The base dependency lock covers the simulator and test dependencies. The
RL and diagnostics extras use declared constraints. Save `pip freeze`
with results to record resolved versions. CPU is the canonical default.
For CUDA use a compatible PyTorch CUDA build and NVIDIA driver, then check
`& $py -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`.
Headless disables the interactive viewer. RGB capture still needs a working
MuJoCo OpenGL context on Windows.

## Run, inspect and recover

```powershell
$area = 'simulation/mujoco/training/autonomous-manipulation'
$run = Join-Path 'simulation/mujoco/runs' ('reach-v6-' + [guid]::NewGuid().ToString('N'))
& $py -u -B "$area/canonical_reach.py" --native-bin build/rl-native/bin/Release --output $run
& $py -m pip freeze | Set-Content (Join-Path $run 'pip-freeze.txt')
$config = Join-Path $run 'environment.json'
$train = Join-Path $run 'training'
Get-Content (Join-Path $train 'report.json')
```

The [canonical protocol](training/autonomous-manipulation/canonical-reach.json)
defines observations, action axes, environment, device, seeds, PPO schedule
and checkpoint frequency. Use `--device cuda` only for a separately reported
device comparison. Use `--prepare-only` to build a fixture without training.
Each invocation creates its own scene, configuration, provenance and output
directories. Inspect `training/steps.csv`, `ppo_updates.csv`, `performance.csv`
and `decisions.jsonl` for progress. A checkpoint stores a policy archive and
SHA sidecar. Keep its sibling `run.json` and its generating configuration.

```powershell
& $py -u -B "$area/reference_reach.py" --config $config --episodes 2
& $py -u -B "$area/run.py" --config $config --objective reach --evaluate-only --warm-start $train --evaluation-seed 920000 --episodes 8 --horizon 64 --device cpu --watch-native
& $py -u -B "$area/run.py" --config $config --objective reach --warm-start-checkpoint (Join-Path $train 'checkpoint-128.zip') --steps 128 --rollout-steps 128 --batch-size 64 --epochs 5 --horizon 64 --seed 7 --evaluation-seed 910000 --episodes 2 --checkpoint-every 64 --ent-coef .005 --device cpu --headless
$diagnostic = Join-Path 'simulation/mujoco/runs' ('report-' + [guid]::NewGuid().ToString('N'))
& $py -B "$area/report_training.py" --output $diagnostic --plots $train
```

The deterministic reference validates the isolated reach target through the
same checks. The [Playground guide](README.md#2-open-the-existing-playground)
covers the separate viewer, manual control and chess transfer workflow.
The [hybrid approach example](examples/qualify_hybrid_approach/README.md)
visualizes deterministic approach and retreat with its fixture. Full-board
lift and transport remain experimental. For the second command above, close
the viewer after inspection. Switch to `--headless` for unattended evaluation.
Warm starts restore policy weights with a fresh optimizer and reset RNG.
For a completed run, use `--warm-start $train` to load the final post-update
policy. A numbered checkpoint captures weights at the decision callback and
can precede the optimization of that rollout. Use it to recover interrupted
runs. The runner checks the source configuration hash. If you intentionally
transfer weights to a changed compatible fixture, pass
`--allow-config-transfer` and report that as a separate experiment.
Keep the same environment JSON and use the recorded training arguments when
comparing continuation runs. Archive integrity and policy-space checks cannot
guarantee bitwise replay across OS, device, driver or library versions.

## Submit a comparable result

Use one directory per run, named for experiment, contributor, seed and date
or a UUID. Submit a short Markdown summary and the generated diagnostic
inventory. Include OS, Python, PyTorch, CUDA and GPU, CPU, seed, config and
model hashes, wall time, steps, training episode successes, and independent
evaluation counts. Record errors and zero-success runs. Include the
configuration, `run.json`, `report.json` or `failure.json`, and portable
diagnostic CSV/JSONL exports. Review exports for private paths and identifiers
before sharing. Record any differing settings explicitly.

Share large checkpoints and datasets in a team-approved artifact store with
SHA-256 and a link in the report. Git LFS is an option if maintainers configure
it. The canonical run regenerates its required scene and checkpoint from
tracked assets and public dependencies. Historical checkpoints remain on the
experiment machine and are optional for reproducing this protocol. The PR
includes portable telemetry and hashes. Keep virtual environments, build
trees, generated meshes, checkpoint binaries and credentials out of Git.

## Troubleshooting

| Symptom | Check |
|---|---|
| CUDA unavailable | Run the Torch check above. Use the CPU protocol or install the matching CUDA wheel and driver. |
| Native build or DLL load fails | Confirm generator, x64 configuration and OpenCV_DIR. Check the three native outputs and OpenCV DLL in the same Release directory. |
| Missing asset or reference | Start at the repository root and regenerate the fixture. Read the missing file path in stderr. |
| Renderer or camera fails | Check OpenGL in the desktop session, framebuffer size, marker layout and camera reference reports. |
| Invalid observations | Check orientation, freshness, RGB localization and the configured actor schema. |
| IK or collision rejection | Inspect validation status and offending geom pair in decisions.jsonl. Retain the collision checks. |
| Action or archive incompatibility | Match environment version, policy version and action/observation spaces. Check the sidecar and source configuration. |
| Training stalls or vanishes | Check worker liveness and heartbeat, stderr, logs and system events. Recover from a verified checkpoint in a fresh output directory. |
| Reward improves without reach success | Compare before/after held-out evaluation and the deterministic reference. Inspect reward components and action acceptance separately. |

See the [training diagnosis](reports/training-diagnostics/README.md) and
[implementation notes](training/autonomous-manipulation/README.md).
