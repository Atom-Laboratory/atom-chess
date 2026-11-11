# ATOM training diagnosis

## Findings

**The PPO updates change weights. Held-out tests have yet to show improved reach success.** The production-style Motion Planner handoff is missing from the training loop. The autonomous trainer starts from a configured pose and validates each policy proposal through native IK and a swept collision check. It cannot teach a local policy from the planner's actual approach endpoint distribution until that handoff is integrated.

For the isolated pawn reach fixture, the deterministic visual reference reached the threshold in 2/2 episodes (17.49 and 17.28 mm against a 17.5 mm threshold). Thus the target can be reached with the available observation and controller in those resets. V4 accepted 1,007/1,024 proposals. A global collision veto cannot account for the zero held-out successes in that run. Full-board conditions differ. The M2 native high approach and retreat passed its qualification, while the M4 local descent contacted the modeled D2 pawn. The isolated head grasp subsequently lost grip during lift. See the [M2 qualification](../../../../docs/camera-rl/hybrid-m2-qualification.md) and [M4 supervision evidence](../../../../docs/camera-rl/hybrid-m4-supervision.md).

## Experiment inventory

| Run | Outcome |
| --- | --- |
| [Overnight workers](overnight/inventory.json) | Seeds 1007/1044 logged 3,003/2,987 decisions and 23 completed episodes each. Zero grasps or lifts. Best recorded gaps were 8.60/10.55 mm. Both saved verified 2,048-decision checkpoints before the session ended around an unclean Windows reboot. The reason for the reboot is unknown. |
| [Recovered workers](recovered/inventory.json) | Seeds 1007/1044 logged 4,438/4,784 decisions, accepted 3,759/4,009 proposals and completed 34/37 episodes. Zero grasps or lifts before being stopped for diagnosis. |
| [Reach v4](reach/9a418ad05a3c4ab285a9a7fd9cabee91/episodes.png) | 1,024 decisions. Evaluation 0/8 before and after. Median best gap 33.133 to 31.339 mm. |
| [Reach v5](reach/8fd65591d4b841c2af8f92b4a299cba0/episodes.png) | 2,048 decisions. One training reach and 0/8 post-training held-out reaches. Median best gap 33.133 to 33.108 mm. Weights changed and the checkpoint reloaded. |
| [Original v6 attempt](history/inventory.json) | Run `39d9240af5124aa2a0eee42fa0aeeb47` stopped before a baseline or optimizer update was recorded. |
| [Canonical v6 smoke](canonical/inventory.json) | Regenerated scene, clean Windows Python and native build, 128 decisions. Baseline and post-training evaluation both 0/2 (median best gap 31.91 to 30.61 mm). Independent evaluation on seeds 920000–920001 gave 0/2. Reloading checkpoint 128 and training 128 more decisions gave 0/2 on the original held-out seeds. |

[History inventory](history/inventory.json) includes completed, failed and incomplete autonomous runs. Each evidence directory contains the archived allowlisted files with local paths pseudonymized. Logs preserve actor actions, applied command traces, rewards and losses when available. `episodes.png` includes rolling success, grasp and lift rates and cumulative reward components. `actions.png` shows per-axis distributions and validation verdicts. `ppo.png` uses update metrics as emitted by the runner. A reach-only episode cannot demonstrate grasp or lift. The evaluation seeds and absolute counts are more informative than small-sample percentages.

## What to investigate next

| Classification | Evidence and next validation |
| --- | --- |
| Confirmed reproducibility defect | Historical configurations require locally generated inputs. Rebuild the canonical fixture from tracked sources and verify a clean run, evaluation and checkpoint load. The workflow tests below exercise that path. |
| Architectural limitation | Native approach and supervised PPO have separate entry points. Execute the approach, verify the handoff and run the local policy from its actual endpoints under fixed seeds. |
| Confirmed training issue | Weights changed with zero held-out reaches in v4 and v5. Compare policy displacements and deterministic visual reach under identical reset seeds. |
| Suspected issue | Reward scale and reset difficulty may suppress useful learning. Change one factor with the same seeds, schema and safety settings. |
| Insufficient evidence | The experiments cannot establish generalization, diagnose the reboot, or attribute the learning plateau to CUDA, observation design or a single hyperparameter. |

- V4 actions had standard deviations of roughly 0.38–0.41 across three normalized axes and saturation below 2%. The samples show exploration, but do not establish that the actor consistently explores useful directions or that its deterministic mean is large enough to approach. Compare proposed and executed displacements by signed axis, including on held-out resets.
- V4 accumulated about +0.78 proximity reward, −10.24 time cost and −80 timeout cost across 16 episodes. The proximity signal existed, but useful progress contributed little on that scale. Canonical v6 sets timeout cost to zero for isolated reach. Its 128-decision result qualifies the workflow. A controlled comparison with the same observations, start distribution and seed set is needed to isolate the reward effect.
- The absence of grasp/lift in overnight logs cannot be explained by the optimizer alone. Successful bilateral contact requires usable pose, wrist/opening and approach geometry together. The first decisive comparisons are a deterministic closed-loop reference in each reset class and a supervised PPO run starting from the same planner approach endpoints. Expand to grasp, lift and transfer only after each preceding gate is repeatable.
- The v6 vector actor receives RGB-derived target geometry and valid flags, task data, and command history. Historic image actor runs used image histories. Differences in action dimensionality, actor features and reward across versions confound comparisons. Use one-factor ablations and retain the same evaluation seeds, geometry, reset budget and safety checks.
- Historical logs cannot recover gradients or prove freshness of every raw frame. The [device probe](device/diagnostic.json) includes a fresh observation snapshot and a synthetic forward/backward/Adam gradient audit. Treat it as a device and wiring check. Measure PPO and environment timings separately.

## Performance and reproducibility

The clean CPU smoke used the installed Windows lock plus RL extras, a fresh x64 MSVC/OpenCV 4.12 native build, and assets regenerated from the repository. 128 rollout decisions including optimization took about 18.58 s (6.9 decisions/s), of which 0.091 s was PPO optimization. A decision can advance multiple MuJoCo integration ticks. Decision throughput and wall-clock physics timings are separate from integration tick rate. Historical logs lack a reliable total for physics integration ticks.

On the RTX 5070 Ti host, the batch-64 synthetic diagnostic measured about 4.84 ms/update on CPU and 6.27 ms on CUDA. Its JSON verifies parameter, input, gradient and Adam-state placement. That probe measures neither end-to-end CUDA throughput nor actual GPU renderer utilization in the clean CPU run. See the hardware samples and stage timings in the inventories for recorded rollout utilization, memory and perception cost. A faster optimizer has little impact on the measured single-environment smoke. Profile camera and native validation before scaling workers.

The original two CUDA workers observed median GPU utilization of 12% and 4%, with roughly 3,071 MiB device-wide GPU memory in both samples and 160 MiB Torch-reserved memory per worker. The host CPU median was about 57%. In each worker, roughly 320 of 508 summed decision-seconds were recorded in perception, 160 in validation and 26 in physics. Perception includes frame acquisition and the vision path. These stage sums do not measure concurrent session wall time or isolate image preprocessing.

Historical PPO dashboard loss records describe updates and may be sparse. Missing statistics remain missing. The sample count, seed and task scope are part of every claimed result. Keep raw checkpoints on the originating machine or in approved artifact storage. Use their SHA-256 for comparison.

The full simulator suite produced 201 passes, 59 skips and one failure with the native Windows Chess Core bridge configured. The failing test was `test_task_plan.py::test_physical_capture_removes_before_attacker` (`GRIP_LOST_DURING_TRANSPORTING`). Without the bridge override the two Chess Core command tests also failed because WSL2 could not start on the host. The native executable resolved those two failures. A deliberate configuration hash mismatch was rejected before training.

Follow the [contribution guide](../../TRAINING_CONTRIBUTION_GUIDE.md) for install, canonical training, held-out evaluation, warm-start and report generation.
