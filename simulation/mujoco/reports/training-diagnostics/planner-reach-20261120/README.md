# Planner-started reach continuation — 2026-11-20

This report is separate from the uncommitted Antigravity narrative. The attached
[summary](summary.json) contains source-report hashes, weight identities, seed
records and local artifact paths; [paired-seeds.csv](paired-seeds.csv) exports the
paired comparison. Run folders/checkpoints remain local and are not distributed
by committing this small evidence inventory.

| Experiment | Result | Interpretation |
| --- | --- | --- |
| v6 BC vs BC+PPO, same 16 seeds 940000–940015 | 12/16 for each | No demonstrated PPO advantage in success rate; neither is 90% qualified |
| v8 deterministic reach after actual planner approach, seeds 960000–960003 | 4/4 | Local reach feasibility only; original wrist/open-finger configuration retained |
| v8 watched PPO pilot | 512 accepted decisions; 20/20 completed training reaches | Weights changed; archive reload verified; optimizer updates logged |
| v8 pilot before/after, seeds 950000–950007 | 8/8 before and 8/8 after | Fine-tuning preserved success; it did not improve an already perfect small-sample baseline |
| v8 final weights, new seeds 950100–950115 | 16/16 | Additional isolated-fixture evidence; still not populated-board or hardware qualification |
| Full-board deterministic reach, seeds 970000–970001 | 0/2, TIME_LIMIT | Approach succeeded; local continuation was blocked by a gripper hull/white queen D1 clearance check |

The v8 median gap was 17.176 mm before and 17.267 mm after; mean return was
15.058 before and 15.028 after; mean duration was 23 local decisions in both.
Do not report these as an improvement in speed or return. The isolated threshold
is 17.5 mm and no grasp, lift or e2-to-e4 transfer was demonstrated.

The full-board rejection distances were approximately 0.883 and 0.950 mm against
a 1 mm conservative clearance. These are predicted clearance violations, not
proof that the real robot hit the queen. The next integration problem is a local
entry/continuation that avoids this neighbor. Do not disable the check or promote
the isolated checkpoint as a populated-board solution.

## Changes and verification

S039 cancels shared rigid motion in nominal pair bounds. S040 adds an opt-in
planner-started, contact-free XYZ reach environment, verified v6-to-v8 weight
transfer and lateral candidates. S041 corrects the scratch-render visibility
reference. Real RGB arrival checks and the version-7 manipulation gate remain.
The dashboard now supports the actual vector-only MLP instead of assuming CNN
image inputs. See the [workflow guide](../../../../../docs/camera-rl/planner-started-reach.md).

The seven selected Python regression modules passed 65 tests, with three
fixture-dependent skips. The native-reach integration fixture was supplied;
its five tests ran. Tests include hidden-physics observation invariance,
no randomized robot start, forbidden contact retention, common rigid motion,
relative-motion collision detection, invalid profiles and CNN/MLP dashboard paths.
Two additional reference-CLI cases then passed with the reach curriculum suite
(7/7): completed unsuccessful episodes now return exit code 1, preventing an
automatic training stage from treating a saved failure report as qualification.

Preserved failures include the initially out-of-bound centered endpoint, a
candidate search exhausted by inconsistent synthetic templates, and a dashboard
error before training. The successful pilot followed those corrections. No
collision geometry, friction, gravity, camera or perception threshold was changed.

These are small, fixed-geometry simulator experiments. A complete game-state
adapter, populated-board local control, grasp/lift qualification and real visual
outcome verification remain separate requirements. Repeated training on these
seeds would make them development data, not independent reliability evidence.
