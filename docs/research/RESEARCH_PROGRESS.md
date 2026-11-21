# ATOM manipulation research progress

Updated: 2026-11-21. This file is the continuation entry point.

## Current phase

Phase 0 historical evidence consolidation and Phase 1 native GPU smoke passed.
Phase 2 robot-model parity is next. No GPU speedup or robot-model physics parity
has yet been established.

## Last measured result

- Full-board reach PPO: 1,024 new decisions, 44/44 completed training reaches,
  8/8 before and after, 16/16 additional reach tests. This is not grasp training.
- Isolated deterministic grasp/lift: measured rise 44.764 mm on seed 970000,
  retained pad contacts, original 32 mm minimum rise. Three additional physical
  tests on seeds 970100–970102 passed. No dedicated extended lifted hold was
  evaluated; this does not yet satisfy the new sustained-hold requirement.
- Best current candidate: canonical MuJoCo 3.17.0, elliptic cone/impratio 10,
  existing full-gripper colliders, model-derived closing preload factor 2.5,
  selected-piece/moving-finger hull clearance zero, other pairs 1 mm, lift speed
  fraction .25, requested travel 1.5 model piece heights. Camera supplies target
  XY; contact/position truth is used for simulation verification/safety.
- Best verified policy remains contact-free planner-started reach; the successful
  grasp is deterministic, not learned.

## Failures retained

Crowded d2 clearance rejection; bounded upper-head search with no valid pair;
isolated slip with the original solver; first-contact closure timeout under
elliptic/10; 31.419 mm lift below the unchanged 32 mm threshold. All remain
distinct from the later isolated success. See EXP-0001 and the linked artifacts.

## GPU configuration

Measured host: RTX 5070 Ti, SM120, 16,303 MiB VRAM, driver 617.14; Windows 10 Pro
19045; Ryzen 5 3600X (6/12), approximately 32 GiB RAM. Existing Torch
2.14.1+cu130 lists sm_120. Installed isolated stack: MuJoCo/MJWarp 3.17.0 and
Warp 1.19.0, reporting bundled CUDA 13.4 and driver 13.4. An actual CUDA array
kernel and primitive contact smoke passed; robot parity is still pending.

## Next actions and gates

1. Finish historical artifact inventory and research catalog coverage.
2. Preserve the passed native smoke: one and sixteen worlds, 500 steps each,
   no overflow flags, final primitive qpos error 5.344e-9.
3. Implement matched, repeated throughput benchmarks; smoke timings are not a
   complete pipeline benchmark.
4. Compare unchanged robot-model forward/step/replay behavior before CEM.
5. Add explicit lifted-hold verification and camera-only command audit. The
   current low-level bias feedforward reads live simulation qfrc_bias; audit and
   replace that privileged command dependency before camera-only control claims.
6. Implement bounded CEM only on a qualified backend and preserve CPU replay.
7. Demonstrations, shared-policy training and curriculum follow measured gates.

Native audit is read-only. Its generic scenario tool changed solver/integrator
in an attached copy and crashed; that output is a tooling limitation, not parity
evidence. No source asset was changed by that audit.

## Documentation and execution status

[RESEARCH_INDEX.md](RESEARCH_INDEX.md) maps decisions, experiments and report
sections. ADRs S046–S052 cover the recent canonical diagnostics; S053 establishes
the isolated GPU research environment. All runs must have finite budgets and
fresh output paths. A completed Watch window is not ongoing training. Background
work is reported only while a verified process is actually running.
