# EXP-0001 — Canonical reach and deterministic grasp baseline

Date: 2026-11-21. Related decisions: S039–S052. Algorithm: SB3 PPO for reach;
deterministic native planner/local supervision for grasp/lift. These are separate
experiments and must not share a combined success rate.

## Question, baseline and evidence

What has actually been demonstrated before GPU acceleration? The
[baseline package](../../../simulation/mujoco/reports/training-diagnostics/crowded-reach-20261121/README.md)
contains retained negative trials, reach CSVs, original artifact paths and hashes.
Historical v6/isolated results remain in the previous diagnostic packages.

Canonical software: MuJoCo 3.17.0, Python 3.12.14, Torch 2.14.1+cu130,
SB3 2.9.2. Host: Windows 10 Pro 19045, Ryzen 5 3600X (6 cores/12 threads),
approximately 32 GiB RAM, RTX 5070 Ti/16 GB. CPU physics is float64.

Reach: 1,024 new PPO decisions; completed training reaches 44/44; paired seeds
980000–980007 give 8/8 both before and after; additional seeds 981000–981015
give 16/16. No PPO advantage is inferred from an already passing small baseline.
Training wall time 514.16 s; optimizer time 1.59 s. Full training configuration,
weights, source and asset identities are in the retained run.json.

Grasp: canonical full-gripper collision geometry; isolated pawn at e2; camera
supplies XY, static compiled model supplies geometric hypotheses. The final
candidate uses elliptic/10, load factor 2.5, selected moving-finger hull margin
zero, other margins 1 mm, lift speed fraction .25 and requested travel 1.5
piece heights. No weld, attachment or live object position supplies a target.
The watched seed 970000 rose 44.764 mm with both pad contacts retained; the
unchanged minimum is 32 mm. Additional regression seeds 970100–970102 passed.
This is deterministic lift evidence, not a learned policy or extended lifted
hold qualification. Simulator measurements verify outcome and safety.

## Failure analysis and limitations

Original soft-contact trials slipped; elliptic/10 initially exposed a
first-contact tracking rejection corrected by S051. The short lift then rose
31.419 mm and correctly failed the 32 mm criterion. The later explicit longer
travel passed that criterion. Crowded insertion still fails. Experimental
geometry/material values are not measured hardware calibration.

## Reproduction and artifacts

Use the baseline package's commands and
[qualify_hybrid_approach README](../../../simulation/mujoco/examples/qualify_hybrid_approach/README.md).
Run `test_native_grasp.py` with `ATOM_NATIVE_GRASP_CONFIG` set to the retained
elliptic/10 isolated fixture. Source identities are the exact file hashes in
each run's provenance, including the precommit working diff; the finalized
implementation is committed separately. Original results are preserved.

Artifact consolidation and dedicated extended-hold evaluation are pending.
