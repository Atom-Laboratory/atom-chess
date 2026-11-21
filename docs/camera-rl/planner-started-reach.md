# Planner-started visual reach

## What changed

This experimental version 8 connects the existing native `ac:motion` approach
to a local PPO reach environment. It replaces randomized robot starts with an
actually executed and verified approach. Version 7 remains an observation-only
grasp/lift handoff; no grasp lease or complete manipulation workspace is enabled.

```text
Prepared ac:chess task / board context
  -> ac:vision RGB and ArUco homography -> estimated piece XY
  -> Python approach adapter -> native ac:motion waypoints and IK
  -> conservative swept checks -> simulated controller execution
  -> tracking and fresh real RGB arrival checks
  -> local MLP proposal -> native IK / velocity / swept checks
  -> controller -> next real RGB observation
```

The task and FEN here come from a prepared fixture. The native motion and vision
libraries are actually called, but this runner does not yet consume live game
events, execute a capture or update the confirmed board through the full game FSM.

## Model and learning

The current vector-only policy is a PyTorch/SB3 actor-critic, not a tree ensemble.
Its actor is `30 -> 64 Tanh -> 64 Tanh -> 3`; the critic has separate 64/64 hidden
layers and a scalar value output. The archive inspected on 2026-11-20 contained
12,551 trainable parameters, including Gaussian action log standard deviations.
This profile has no CNN or Transformer. Other historical pixel policies do.

Behavioral cloning initializes the actor by regressing toward a deterministic
visual reference's proposed actions. PPO then collects simulated transitions,
estimates advantages and updates the Gaussian actor with its clipped objective;
the critic learns discounted returns. Adam/backpropagation changes the weights.
The transferred policy is an initialization, with a fresh optimizer, not a resume.

Actor inputs are camera-derived target features, logical source/target and piece
context, issued commands and previous action. Static board calibration and model
piece height provide geometry; monocular RGB supplies no independent depth
measurement. Simulated joint/body states, pad gap, contacts, rewards and planner
diagnostics remain outside the actor payload. The simulator is used by the
independent training feedback and validation. This does not qualify hardware
tracking when the only real sensor is a camera.

## Planning improvements

- S039 removes common rigid-ancestor motion from nominal pair-distance bounds.
  Common rotation cannot change the distance between two attached shapes.
  Relative motion and custom carried-object bounds remain conservative.
- Lateral approach candidates use board-square offsets and the same fixed camera.
  Their generated trajectory still passes IK, swept checking and live execution.
- S041 compares scratch previews against an unoccluded template of that same
  estimated scene. It does not compare quantized synthetic piece positions to an
  inconsistent centered template. Real arrival validation remains independent.
- Version 8 holds the approach wrist, elbow branch and open-finger commands.
  Selected-piece pad contact is forbidden for this reach-only experiment.

The proposal radius around visual XY/static piece-top height is experimental.
It is not a proof that the entire region is clear; each action is checked again.
The preview template never becomes the actor's actual camera frame.

## Reproduce from the repository root (PowerShell 7)

Prerequisites: the MuJoCo Python environment including RL/diagnostics dependencies,
native motion and vision DLLs, and a prepared canonical version-6 fixture. Follow
the autonomous training README and `canonical_reach.py --prepare-only` if needed.
The source path below is a local fixture example, not a tracked input asset.

```powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$area = 'simulation/mujoco/training/autonomous-manipulation'
$source = 'simulation/mujoco/runs/canonical-v6-baseline/environment.json'
$case = Join-Path "$area/runs" ('planner-reach-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $case | Out-Null
$cfg = Get-Content $source -Raw | ConvertFrom-Json
$cfg.autonomous.PSObject.Properties.Remove('start_radius_squares')
$cfg.autonomous | Add-Member -NotePropertyName start_mode -NotePropertyValue native_reach
$cfg.autonomous | Add-Member -NotePropertyName require_visible_target -NotePropertyValue $true
$cfg.autonomous | Add-Member -NotePropertyName approach_max_candidates -NotePropertyValue 256
$cfg.autonomous | Add-Member -NotePropertyName approach_entry_offsets_squares -NotePropertyValue @(
  @(1.,0.), @(-1.,0.), @(0.,1.), @(0.,-1.),
  @(1.,1.), @(1.,-1.), @(-1.,1.), @(-1.,-1.), @(0.,0.))
$config = Join-Path $case 'environment.json'
$cfg | ConvertTo-Json -Depth 12 | Set-Content $config -Encoding utf8
& $py -u -B "$area/reference_reach.py" --config $config --episodes 4 --seed 960000 --output "$case/reference"
if ($LASTEXITCODE -ne 0) { throw 'Inspect reference failure evidence before training' }
# Review success counts in reference/report.json as well as process exit status.
# Supply a verified version-6 source run; never select it merely by modification time.
$previous = 'simulation/mujoco/runs/ppo-fine-tuned-v6'
& $py -u -B "$area/run.py" --config $config --objective reach --horizon 64 `
  --warm-start $previous --allow-config-transfer --allow-reach-handoff-transfer `
  --steps 512 --rollout-steps 128 --batch-size 64 --epochs 5 `
  --learning-rate .0001 --ent-coef .001 --checkpoint-every 128 `
  --evaluate-before --episodes 8 --evaluation-seed 950000 `
  --device cpu --watch-native --dashboard --output "$case/ppo"
```

Keep the first before/after seed set fixed for development; reserve a different
set for independent assessment. To continue a completed **version-8** run, use
its identical configuration and `--warm-start <case/ppo>` with a fresh output.
The version-6 transfer flag is unnecessary when source/target versions match.
CPU is deliberate for this small MLP; camera rendering/perception and planning,
not network size alone, dominate end-to-end speed. Native watch stays open after
saving the report; closing it ends the viewer. Do not run a second training
window merely because the first has completed and is waiting for closure.

## Inspect and test

`run.json` records configuration/source/assets and initialization weight hashes.
`baseline.json` and `report.json` hold paired before/after outcomes. CSVs and
`decisions.jsonl` contain actual actions, reward components and optimizer metrics.
Each native-reach terminal record identifies its executed approach signature,
issued endpoint and fresh arrival sequence. Reference reports preserve complete
handoff evidence, including failures in `failure.json`. No archive is overwritten.

```powershell
$env:ATOM_NATIVE_REACH_CONFIG = (Resolve-Path $config).Path
& $py -B -m pytest -p no:cacheprovider simulation/mujoco/tests/test_planner_reach.py `
  simulation/mujoco/tests/test_collision.py simulation/mujoco/tests/test_approach_handoff.py `
  simulation/mujoco/tests/test_hybrid_approach.py simulation/mujoco/tests/test_reach_curriculum.py `
  simulation/mujoco/tests/test_ppo_dashboard.py simulation/mujoco/tests/test_autonomous_manipulation.py -q
```

Reach success is a mean pad-gap threshold, not grasp, lift or e2-to-e4 transfer.
Small seed counts cannot establish 90% reliability or sim-to-real readiness.
The next gate is repeatable contact/grasp/lift with independent outcome checks;
never turn the observation-only manipulation flags on to bypass it.

See ADRs [S039](../../simulation/docs/adrs/S039-shared-rigid-motion-sweep-bounds.md),
[S040](../../simulation/docs/adrs/S040-planner-started-contact-free-reach.md) and
[S041](../../simulation/docs/adrs/S041-estimated-scene-visibility-template.md).

The [2026-11-20 results](../../simulation/mujoco/reports/training-diagnostics/planner-reach-20261120/README.md)
preserve the isolated pilot and the initial failed full-board continuation.
The [2026-11-21 follow-up](../../simulation/mujoco/reports/training-diagnostics/crowded-reach-20261121/README.md)
records the later full-board reach update, 16 additional successful reach tests,
checkpoint recovery and the separate failed grasp/lift diagnostics. The later
reach result does not turn those manipulation failures into successes.
