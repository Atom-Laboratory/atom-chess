# Experiment laboratory: run, measure, debug, reproduce

Current camera-guided implementation and test commands are in the
[MuJoCo README](../../simulation/mujoco/README.md). The material below records the
earlier v3 study baseline or its theoretical foundations.

This page is an operating and scientific-method guide. Existing commands are
marked **available**. New evaluation/instrumentation features are marked
**planned**. Do not assume a proposed metric is already present in an output.

## 1. Specify a question before a run

A useful experiment asks: "Does observation history reduce grip loss under the
same start distribution?" or "Does reward version B improve held-out successful
lift rate under an equal data budget?" An unhelpful question is "Will more steps
make the robot good?" Write the hypothesis, alternative explanation, controlled
variables, resource budget and decision rule before seeing the result.

For the first ATOM stage, the question is narrower: can the current policy retain
a prepared grip and lift the E2 pawn under small initial arm offsets? It does not
ask whether the robot can identify any chess piece, pick it or move it to a goal.

## 2. Capture provenance

Preserve the Git commit and dirty-file diff, environment version, complete
resolved hyperparameters, model and asset hashes, camera/render configuration,
reset distribution, training seed, library/device versions and wall-clock budget.
The current run/report files capture a subset, not all of these. In particular,
resolved library defaults and the complete source snapshot are not automatically
exported today. Record them in the experiment note when comparing runs.

Use a new directory. The trainer rejects an existing output directory. Checkpoints
are not small source files: keep them under ignored runs storage and keep small,
versioned result reports in documentation. A result without a reconstructible
configuration is a useful anecdote, not a reproducible comparison.

## 3. Start a run — available

From the repository root in Windows PowerShell:

```powershell
# Visible local lift: starts with a prepared grip.
& ./simulation/mujoco/scripts/Start-RLTraining.ps1 -Stage lift -Steps 20000 -Device cuda

# New local grasp experiment: no prepared contact; no automatic lift warm-start.
& ./simulation/mujoco/scripts/Start-RLTraining.ps1 -Stage grasp -Steps 100000 -Device cuda

# Omit UI pacing for data collection. Rendering the policy image still occurs.
& ./simulation/mujoco/scripts/Start-RLTraining.ps1 -Stage lift -Steps 20000 -Device cuda -Headless
```

Do not run all three commands simultaneously as a benchmark. A visible viewer
and background jobs compete for resources. `-Device cuda` checks availability;
it does not move ordinary MuJoCo dynamics onto the GPU. Check policy/device
metadata before claiming GPU use. "Headless" here means no interactive windows,
not no image rendering or no graphics-context requirement.

The [operator guide](../hybrid-control/visual-grasp-rl-guide.md) documents setup,
controls, stopping, resuming and replay. The UI speed is a pacing limit, not an
optimizer learning-rate setting. Check real throughput rather than estimating
completion from the GPU model or nominal simulation speed.

## 4. Read the outputs — available

| File | Meaning | Common misinterpretation |
|---|---|---|
| run.json | Environment/config, requested steps, seed, watch and resume source | It does not contain every inherited PPO default |
| progress.json | Atomic current status and cumulative steps; counts for this process | Training success rate is not held-out performance |
| episodes.jsonl | One terminal record per completed training episode | Final lift is not maximum lift; no full trajectory is stored here |
| checkpoint-N.zip | Periodic policy/optimizer snapshot | It is not necessarily a completed or evaluated policy |
| policy.zip | Final or gracefully stopped model | Existence is not successful learning |
| report.json | Device, hashes, updated parameters, evaluation and hold baseline | A stopped run skips evaluation and has success_rate=null |
| failed-policy.zip | Saved from an exception inside the learning call | It does not convert a failed run into a qualified result |

Current statuses include training, evaluating, completed, stopped and failed.
During evaluation the interactive training windows close. Allow the evaluation
and report write to finish before treating the process as complete. Some errors
before the learning call can still leave partial setup files without a final
report; inspect stderr and process exit status.

For a known run directory:

```powershell
$atomRun = 'PATH_TO_RUN'
Get-Content (Join-Path $atomRun 'progress.json')
Get-Content (Join-Path $atomRun 'report.json')
$atomEpisodes = Get-Content (Join-Path $atomRun 'episodes.jsonl') | ForEach-Object { $_ | ConvertFrom-Json }
$atomEpisodes | Select-Object -Last 10 step,episode_index,success,disturbed,lift_m,held
```

Training counts reset in a new process, even when the global timestep counter is
restored from a checkpoint. A resumed run's `trained_steps` is cumulative; the
requested steps are additional. PPO can round data collection to rollout-sized
chunks. Resume restores policy/optimizer, not the exact previous simulation,
rollout buffer or all random-generator states.

## 5. Stop, resume and replay — available

Use the UI's Stop and save checkpoint or close the viewer. Another supported
request is an empty STOP file inside the run directory:

```powershell
New-Item -ItemType File -Path (Join-Path $atomRun 'STOP')
```

The current check occurs during training callbacks. A STOP file is not a universal
interrupt for setup, a paused UI loop or final evaluation. Use the UI Stop button
to exit its pause loop. A forced process kill may lose work since the last save.

After a completed/stopped report exists, use a **new** output directory:

```powershell
& ./simulation/mujoco/scripts/Start-RLTraining.ps1 -Stage lift -Steps 20000 -Device cuda -Resume PATH_TO_RUN
& ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/training/grasp-lift/evaluate.py --bundle simulation/mujoco/assets/bundles/playground-fingertip-only-v1 --run PATH_TO_RUN --seed 10000
```

Resume verifies model/environment/stage/horizon and recorded checkpoint hash.
Changing stage or reward needs a new experiment, not a relabeled resume. Replay
uses CPU inference and one deterministic episode; it is inspection, not the broad
evaluator proposed in G1. Earlier environment-version checkpoints need matching
historical code, not current semantics.

## 6. Compare independent training seeds — available but budgeted

Use the Python CLI for settings the PowerShell launcher does not expose, such as
training seed or evaluation-episode count. Example for one additional experiment:

```powershell
$atomRun = Join-Path 'simulation/mujoco/runs' ('lift-seed17-' + [guid]::NewGuid().ToString('N'))
& ./simulation/mujoco/.venv/Scripts/python.exe -u simulation/mujoco/training/grasp-lift/run.py --bundle simulation/mujoco/assets/bundles/playground-fingertip-only-v1 --output $atomRun --stage lift --steps 20000 --seed 17 --eval-episodes 20 --device cuda
```

This command starts another real experiment; it is not required while the current
job is running. The built-in evaluator uses a consecutive sequence starting at
seed 10000 and deterministic inference. More such seeds still test the same tiny
reset family. Keep a separate frozen final test set when developing a broader
evaluator. Do not pick the best seed and report it as representative.

## 7. Metrics and uncertainty

Report outcomes independently of reward. Use at least success rate, failure
categories and evaluation sample count. Separate runtime, task duration and data
collection throughput. For broad manipulation add maximum disturbance, unwanted
contacts, drop rate, placement pose error, release/support confidence and recovery
rate. These extra metrics are **planned**, not all fields in current reports.

A success fraction p_hat=k/n is an estimate. A two-sided Wilson interval with
z=1.96 has center and half-width:

    denominator = 1 + z*z/n
    center = (p_hat + z*z/(2*n))/denominator
    half_width = z*sqrt(p_hat*(1-p_hat)/n + z*z/(4*n*n))/denominator

For 5/5 successes the lower endpoint is only about 0.566. Five attractive videos
therefore do not establish 95% reliability. Reset episodes can be correlated;
training-seed variability is a second source of uncertainty. Use paired reset
seeds when comparing policies, and distinguish within-policy sampling from
between-training-run variation. For broader methodological context see [Agarwal
et al.](https://arxiv.org/abs/2108.13264).

An observed >=95% rate is not the same as a confidence lower bound >=95%.
State which criterion a gate uses. Never combine different reward versions,
reset distributions or stage labels into one success denominator.

## 8. Debug by failure, not by algorithm popularity

| Observation | First checks | Evidence to collect |
|---|---|---|
| No learning signal | Reward scale/sign, reachable task, action effects, episode boundaries | A scripted feasibility probe and reward decomposition |
| High reward but no success | Reward exploit, too-easy partial progress, weak success predicate | Replay highest-reward failures; compare against hold |
| Good training, poor evaluation | Stochastic vs deterministic behavior, seed leakage, overfitting | Same-seed paired evaluations and held-out distributions |
| Lift works, grasp fails | Prepared grip versus approach/closure, alignment, contact model | Per-phase traces; reset vs action-induced disturbance |
| Pixels seem irrelevant | Fixed task, near-constant optimal action, hidden reset shortcut | Constant-image and open-loop baselines |
| Unstable physical scene | Units, mass/inertia, contact masks, timestep, gains | Passive settling and isolated contact tests |
| GPU mostly idle | Single-environment rendering/reset/CPU bottleneck | Wall time per render, physics, inference and update |
| Viewer looks frozen | Paused UI, optimizer work, blocking setup, error log | progress status plus process stdout/stderr |
| Resume rejected | Version, stage, horizon, model/checkpoint hash | Compare run.json and report.json; never bypass checks blindly |

PPO logs such as value loss, approximate KL, clipping fraction and entropy are
diagnostics, not acceptance metrics. Large value loss can reflect reward scale;
small KL can reflect almost no useful policy change. Entropy loss may be printed
with a negative sign. Interpret the exact implementation rather than attaching
"good" and "bad" labels to a plot direction.

## 9. Ablation plan — planned evaluation tooling

Change one factor at a time where possible: reward, reset range, camera input,
control period, encoder or algorithm. Use equal environment-step budgets and also
report wall time. Add multiple factors deliberately only with an experiment design
that can identify their interactions. If a simulator geometry change makes the
task easier, label it a task change, not an optimizer improvement.

For observation dependence, compare normal, constant and delayed frames, and
include an open-loop action baseline. For contact fidelity, compare fingertip
proxies against measured alternative geometry after independent physical tests.
For a new learner, retain the same task and held-out protocol. The simulator's
own feedback oracle is appropriate for scoring experiments, but is not evidence
that real camera feedback works.

## 10. Experiment note template

```text
Question / hypothesis:
Expected alternative explanations:
Code commit and dirty changes:
Environment version / stage / task distribution:
Bundle and checkpoint hashes:
Observation, action units and decision frequency:
Reward, terminal and truncation rules:
Resolved algorithm settings and software/device:
Training seeds / validation seeds / final test seeds:
Baseline / treatment / data and wall-time budgets:
Primary outcome / disturbance outcomes / confidence method:
Observed result, including failed or interrupted runs:
Failure analysis and video/trace locations:
Claim supported / claim not supported:
Next experiment and stopping rule:
```

## 11. Sustainable scaling

Profile before vectorizing. Independent simulation workers, rendering contexts,
GPU memory and process startup can dominate a small image policy. More workers
can improve sampling throughput while changing optimization statistics and the
meaning of callback/save intervals. MJX or a different physics backend is an
architectural experiment with new contact/model validation obligations, not a
free GPU switch for the current Simulation class. Keep a single-process reference
implementation to identify semantic differences after optimization.
