# ATOM manipulation research progress

Updated: 2026-11-21. This file is the continuation entry point.

## Current phase

Phase 0 captured the historical inventory; catalog consolidation remains open.
Phase 1 native GPU smoke passed.
Phase 2 forward/step screen and recorded canonical grasp/hold replay passed in
their limited scopes. Phase 3 physics-only benchmarks ran through 1024 worlds.
Phase 4 bounded isolated CEM pilot and checkpoint continuation passed. Frozen
candidate evaluation passed on one additional camera entry after a failed first
entry attempt and a same-seed headless retry. Phase 7 exported two verified
camera/command demonstrations. Phase 8 now has a bounded shared BC/PPO parameter
policy pilot (EXP-0008). Broad generalization, sequential visual servoing and
end-to-end RL acceleration are not established.

## Last measured result

- Full-board reach PPO: 1,024 new decisions, 44/44 completed training reaches,
  8/8 before and after, 16/16 additional reach tests. This is not grasp training.
- Historical isolated deterministic grasp/lift: rise 44.764 mm on seed 970000,
  retained pad contacts, original 32 mm minimum rise. Three additional physical
  tests on seeds 970100–970102 passed. No dedicated extended lifted hold was
  evaluated; this does not yet satisfy the new sustained-hold requirement.
- Canonical deterministic reference: MuJoCo 3.17.0, elliptic cone/impratio 10,
  existing full-gripper colliders, model-derived closing preload factor 2.5,
  selected-piece/moving-finger hull clearance zero, other pairs 1 mm, lift speed
  fraction .25, requested travel 1.5 model piece heights. Camera supplies target
  XY; contact/position truth is used for simulation verification/safety.
- The original contact-free planner-started reach policy remains separate. A new
  experimental macro policy learns three isolated grasp timing/preload parameters
  while retaining deterministic native trajectory generation (EXP-0008).
- New controller seed 970200: lift plus 1.02 s held interval, final rise 44.687 mm,
  sampled hold drop .270 mm. Full CPU tape replay is exact; 1/16 GPU replay worlds
  passed physical checks. Identical tapes are not independent trials (EXP-0004).
- Fixed-control benchmark at 1024: GPU median 1,424,059 world-steps/s; six-thread
  CPU 124,632 (11.43×). Excludes camera, planning, policy, resets and rendering;
  this is not a measured RL speedup (EXP-0005).

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
kernel and primitive contact smoke passed. Robot forward/single-step and recorded
held-lift replay passed in the scopes recorded in EXP-0003/0004.

## Next actions and gates

1. Finish historical artifact inventory and research catalog coverage.
2. Preserve the passed native smoke: one and sixteen worlds, 500 steps each,
   no overflow flags, final primitive qpos error 5.344e-9.
3. Fixed-control benchmarks completed; full pipeline throughput is unmeasured.
4. Canonical recording and 1/16-world replay passed; new candidate paths still
   require their own geometric/physical checks.
5. Static command-derived gravity and lifted-hold checks are implemented.
   Camera-only outcome verification remains unqualified.
6. Bounded isolated CEM and independent CPU replay completed; next assess broader
   randomized states and occupied-board geometry.

Current CEM: population 8 ×2 generations, 7/8 then 8/8 physically valid held
lifts, followed by a checkpoint-resumed generation with 8/8. Canonical winner
replay passed. A later hash-bound population 4 ×2 also passed. These are command
search evaluations from one entry, not a neural policy or a reliability sample.
Frozen-parameter evaluation passed on the completed seed-970201 headless retry:
CPU minimum held rise 44.162 mm, maximum hold drop .311 mm, bilateral hold 1 s,
no forbidden engine contact. The first watched entry stopped on camera age
during descent. These are two attempts of one seed, not independent trials.
7. Two isolated demonstrations exported after exact canonical re-execution:
   seeds 970200/970201, 161/147 RGB-action chunks. Actor inputs contain only
   camera, signed camera geometry, task/phase and issued commands; actual state/
   contact data are separate. The first combined export/Watch process crashed
   natively after successful export; presentation moved to a separate worker.
   See EXP-0007. Separate-process Watch passed two complete replay cycles.
8. Shared BC/PPO macro-policy pilot completed: 24/24 training episodes, followed
   by an optimizer/RNG-resumed 4/4. The mean policy passed paired CPU/GPU checks
   on training/validation entries before and after PPO. Duration decreased from
   16.094 to 14.832 s; BC already passed, so no success-rate improvement is claimed.
9. Frozen update-4 policy passed one new seed-970202 camera entry on CPU/GPU:
   minimum held rise 43.793 mm, maximum drop .312 mm, bilateral hold 1 s and no
   forbidden engine contact. This remains a small isolated conditional test.

Latest Stage A checkpoint (different schema from reach/camera PPO ZIP models):
`simulation/mujoco/accelerated/runs/EXP-0008/RUN-shared-parameter-resume-2644d927be2b4f83936aee61708f8862/policy.pt`.
SHA-256 `f56f6e2d0c0e36539cc78748393b8e5d39b6578692b5fbe13ef668ff01ee9428`.
Both bounded training runs and their Watch replays have completed. There is no
unattended/overnight training still running.

Next gate: quantify sparse-neighbor entry feasibility, then acquire independent
camera-localized contexts for curriculum learning. Do not keep increasing isolated
episodes as a substitute for resolving occupied-board geometry. Camera-only
outcome verification and hardware calibration remain open.

Native audit is read-only. Its generic scenario tool changed solver/integrator
in an attached copy and crashed; that output is a tooling limitation, not parity
evidence. No source asset was changed by that audit.

## Documentation and execution status

[RESEARCH_INDEX.md](RESEARCH_INDEX.md) maps decisions, experiments and report
sections. ADRs S046–S052 cover the recent canonical diagnostics; S053 establishes
the isolated GPU research environment. All runs must have finite budgets and
fresh output paths. A completed Watch window is not ongoing training. Background
work is reported only while a verified process is actually running.
