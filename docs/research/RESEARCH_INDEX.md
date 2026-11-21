# ATOM manipulation research index

This is the navigation entry point for the future technical report. Read
[RESEARCH_PROGRESS.md](RESEARCH_PROGRESS.md) for current execution state.

## A. Research overview

ATOM must transform a Chess Core source/destination request and camera-derived
board geometry into physical manipulation through Motion Intelligence and the
low-level controller. Simulation truth may evaluate contacts, slip, topples and
outcomes, but must not supply target coordinates to the deployable actor.

[VERIFIED-RESULT] Contact-free planner-started reach now passes the retained
small full-board test sets. A deterministic isolated pawn lift passed one watched
trial and three additional physical regression seeds. Neither establishes
occupied-board manipulation, a learned grasp or real-robot readiness. Dedicated
held lifts and CPU/GPU recorded replays were subsequently measured in EXP-0004;
a frozen candidate passed one additional isolated camera entry in EXP-0006.
Details: [EXP-0001](experiments/EXP-0001-canonical-baseline.md).

## B. ADR catalog

The canonical directory is [simulation/docs/adrs](../../simulation/docs/adrs).
Historical numbering contains existing duplicate S010/S011 IDs; refer to the
full filenames and preserve their history. New decisions continue after S052.

| ADR | Decision area | Status/scope | Experiments | Report relevance |
| --- | --- | --- | --- | --- |
| S039–S045 | Sweeps, native reach, RGB registration and preshape | Experimental CPU reach; see original records | EXP-0001 | System, methodology, baseline |
| [S046](../../simulation/docs/adrs/S046-lateral-entry-grasp-diagnostic-envelope.md) | Lateral entry diagnostic limits | Experimental; no RL admission | EXP-0001 | Grasp methodology |
| [S047](../../simulation/docs/adrs/S047-upper-sphere-pad-edge-grasp-diagnostic.md) | Transformed pad geometry and upper-head proposals | Experimental, including corrected axis assumption | EXP-0001 | Geometry and negative results |
| [S048](../../simulation/docs/adrs/S048-settled-grasp-hold-before-lift.md) | Consecutive grasp contact window | Adopted diagnostic check | EXP-0001 | Outcome metrics |
| [S049](../../simulation/docs/adrs/S049-selected-finger-near-contact-clearance.md) | Explicit selected-finger near-contact margin | Opt-in diagnostic only | EXP-0001 | Collision constraints |
| [S050](../../simulation/docs/adrs/S050-controlled-grasp-contact-solver-comparison.md) | Fresh controlled contact-solver fixtures | Experimental comparison | EXP-0001 | Physics methodology |
| [S051](../../simulation/docs/adrs/S051-partial-contact-during-coupled-finger-closure.md) | Loaded partial contact while closing | Adopted supervision fix | EXP-0001 | Control and findings |
| [S052](../../simulation/docs/adrs/S052-diagnostic-lift-travel-margin.md) | Lift target versus measured rise | Explicit diagnostic parameter | EXP-0001 | Lift verification |
| [S053](../../simulation/docs/adrs/S053-isolated-native-mjwarp-research-backend.md) | Version-matched isolated MJWarp backend | Accepted design; performance/parity unverified | EXP-0002 | Parallel acceleration |
| [S054](../../simulation/docs/adrs/S054-complete-state-cpu-gpu-parity-boundary.md) | Full state reset and CPU/GPU comparison | Accepted; limited forward/step screen passed | EXP-0003 | Physics validation |
| [S055](../../simulation/docs/adrs/S055-command-derived-gravity-feedforward.md) | Command-derived gravity support | Accepted; canonical held-lift passed | EXP-0004 | Sensor/control boundary |
| [S056](../../simulation/docs/adrs/S056-matched-robot-physics-benchmark.md) | Matched physics benchmarks | Accepted; bounded measurements | EXP-0005 | Acceleration results |
| [S057](../../simulation/docs/adrs/S057-recorded-physics-and-sustained-lift.md) | Full transitions and dedicated lifted hold | Accepted; CPU/GPU replay measured | EXP-0004 | Verification and datasets |
| [S058](../../simulation/docs/adrs/S058-bounded-isolated-cem-grasp-pilot.md) | Bounded Stage A CEM | Accepted; short pilot and CPU winner replay passed | EXP-0006 | Grasp optimization |
| [S059](../../simulation/docs/adrs/S059-shared-model-grasp-geometry.md) | Shared geometry without rendering imports | Accepted; unchanged extraction tested | EXP-0006 | Reproducible infrastructure |
| [S060](../../simulation/docs/adrs/S060-camera-command-demonstration-boundary.md) | Causal camera/command demonstrations and separate Watch | Accepted; two isolated CPU re-executions exported | EXP-0007 | Demonstrations and observation boundary |
| [S061](../../simulation/docs/adrs/S061-shared-parameter-policy-stage-a.md) | Shared BC/PPO macro parameter policy | Accepted; bounded isolated pilot and frozen-entry checks | EXP-0008 | Learning methodology and limitations |

The [complete tracked ADR catalog](ADR_CATALOG.md) and
[historical evidence review](HISTORICAL_EVIDENCE_REVIEW.md) preserve original
conclusions and distinguish inventory coverage from independently checked results.

## C. Experiment catalog

| ID | Question | Related ADRs | Date | Measured outcome | Artifacts |
| --- | --- | --- | --- | --- | --- |
| [EXP-0001](experiments/EXP-0001-canonical-baseline.md) | What is the measured CPU reach/grasp baseline? | S039–S052 | 2026-11-21 | Reach 8/8 paired, 16/16 additional; isolated deterministic lift observed; crowded entry unresolved | [Baseline package](../../simulation/mujoco/reports/training-diagnostics/crowded-reach-20261121/README.md) |
| [EXP-0002](experiments/EXP-0002-native-gpu-environment.md) | Can the measured SM120 host execute pinned native MJWarp? | S053 | 2026-11-21 | CUDA kernel and primitive contact passed at 1/16 worlds; robot parity unverified | [Raw smoke reports](../../simulation/mujoco/accelerated/reports/EXP-0002) |
| [EXP-0003](experiments/EXP-0003-robot-physics-parity.md) | Does unchanged robot forward/step physics agree? | S054 | 2026-11-21 | Two states passed; full contact-rich rollout pending | [Raw parity report](../../simulation/mujoco/accelerated/reports/EXP-0003/robot-forward-step.json) |
| [EXP-0004](experiments/EXP-0004-canonical-held-lift-and-gpu-replay.md) | Does the corrected controller lift/hold and replay? | S054/S055/S057 | 2026-11-21 | Canonical 1.02 s hold; tape passed at 1/16 worlds | [Raw replay reports](../../simulation/mujoco/accelerated/reports/EXP-0004) |
| [EXP-0005](experiments/EXP-0005-physics-batching-benchmark.md) | When does GPU batching help fixed-control robot physics? | S056 | 2026-11-21 | 1–1024 worlds measured; 1024 GPU median approximately 11.43× six-thread CPU | [Raw reports and figure](../../simulation/mujoco/accelerated/reports/EXP-0005) |
| [EXP-0006](experiments/EXP-0006-isolated-cem-command-search.md) | Can bounded CEM find physically verified isolated command plans? | S058/S059 | 2026-11-21 | 7/8 then 8/8; resumed 8/8; frozen CPU/GPU candidate passed one new entry after failed first attempt | [Raw candidate results](../../simulation/mujoco/accelerated/reports/EXP-0006) |
| [EXP-0007](experiments/EXP-0007-camera-command-demonstrations.md) | Can physical experts be exported without actor state leakage? | S060 | 2026-11-21 | Two exact CPU trajectory re-executions, 161+147 causal RGB/action chunks | [Raw demonstration reports](../../simulation/mujoco/accelerated/reports/EXP-0007) |
| [EXP-0008](experiments/EXP-0008-shared-stage-a-parameter-policy.md) | Can a shared camera-feature policy reproduce isolated planner grasps? | S061 | 2026-11-21 | 24+4 physical training macro episodes passed; paired CPU/GPU checks and one additional frozen entry passed; no broad generalization claim | [Raw losses/episodes/reports/figure](../../simulation/mujoco/accelerated/reports/EXP-0008) |

## D. Research findings

- **RF-0001 [VERIFIED-RESULT]:** reach, grasp and lift are distinct outcomes.
  Full-board reach successes coexist with rejected crowded descents (EXP-0001).
- **RF-0002 [VERIFIED-RESULT]:** a bilateral-only tracking exception can prevent
  coupled-finger closure at first unilateral contact. S051 corrected that
  phase-specific supervision defect; this does not relax lift contact requirements.
- **RF-0003 [VERIFIED-RESULT]:** fixed-control physics at 1024 worlds reached
  11.43× six-thread CPU throughput (EXP-0005). End-to-end candidate/RL speedup
  remains unmeasured; isolated CEM feasibility is measured separately (EXP-0006).

## E. Figures and tables catalog

| ID | Caption/metric | Source | Scope |
| --- | --- | --- | --- |
| TAB-0001 [REPORT-TABLE] | Reach success counts and median mean-pad gap, mm | EXP-0001, reach-evaluation.csv | Paired and additional evaluation, not grasp |
| FIG-0001 [REPORT-FIGURE] | Fixed-camera view at rejected crowded descent boundary | EXP-0001, camera-crowded-rejected-descent.png | Negative result, no descent execution |
| FIG-0002 [REPORT-FIGURE] | Isolated closure viewed by the fixed camera | EXP-0001, camera-isolated-closure.png | Occluded contact; not visual lift verification |
| FIG-0003 [REPORT-FIGURE] | Repeated CPU/GPU fixed-control physics throughput and allocation pool | EXP-0005, unsmoothed samples and SVG/PDF/PNG | Physics only; not training throughput |
| FIG-0004 [REPORT-FIGURE] | BC/PPO losses, raw macro rewards and paired CPU execution durations | EXP-0008, source-hashed CSV/JSON, SVG/PDF/PNG | Tiny isolated parameter-policy pilot; one training entry |

## F. Open scientific questions

How much of grasp slip depends on solver regularization versus actual friction
and geometry? Which occupied-board entry paths remain physically feasible?
Can CPU/GPU preserve the relevant contact outcomes? Can RGB and issued commands
support correction through arm occlusion? What measured domain variations are
needed before transferring a policy to the actual assembled arm?

## G. Report preparation guide

| Report section | Current evidence or planned contribution |
| --- | --- |
| 1. Introduction | Manipulation task and physical/logical state separation |
| 2. Related work | Official MuJoCo/MJWarp references; previous RL reading guides |
| 3. Robotic system and simulation | CAD/proxy limitations, model hashes, S046–S052 |
| 4. Methodology | Camera/native planner handoff, metrics and controlled comparisons |
| 5. Parallel acceleration | S053/S054/S056, EXP-0002–0005; physics-only measurements |
| 6. Grasp optimization | S058/S059, EXP-0006; bounded isolated CEM and frozen-entry test |
| 7. Reinforcement Learning | Existing reach PPO baseline; EXP-0008 isolated shared parameter-policy pilot |
| 8. Experiments | EXP catalog, seeds, raw artifacts and reproduction commands |
| 9. Results | TAB-0001, FIG-0001/2 and verified isolated lift scope |
| 10. Discussion | Contact/control/geometry causes remain separate |
| 11. Limitations | No crowded grasp, broad policy generalization or hardware validation yet |
| 12. Conclusions | State only measured outcomes; no inferred speedup or reliability |
