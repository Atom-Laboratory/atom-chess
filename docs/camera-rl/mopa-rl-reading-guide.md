# Reading MoPA-RL for the ATOM architecture

Read this alongside the [proposed ATOM architecture](hybrid-motion-learning.md)
and its [evidence record](autonomous-reach-results.md). It supports an engineering
comparison. ATOM's current PPO experiment has its own observation and execution
contracts and requires its own qualification.

## Main reference

Yamada et al., *Motion Planner Augmented Reinforcement Learning for Robot
Manipulation in Obstructed Environments*, CoRL 2020, published in PMLR volume
155 in 2021, pages 589–603. [Publication page](https://proceedings.mlr.press/v155/yamada21a.html)
and [open PDF](https://proceedings.mlr.press/v155/yamada21a/yamada21a.pdf).

MoPA-RL extends a policy's action space. Small joint-displacement actions
execute directly, while larger proposals invoke planning. Its illustrated
implementation uses SAC and RRT-Connect. Read Algorithm 1 for transitions
spanning several execution steps, and Section 3.3 for action rescaling.
Inspect Section 3.5 and Appendix A.4 for handling invalid proposals, and the
ablations for evidence supporting each mechanism. The experiments are the
authors' simulated tasks. [Paper](https://proceedings.mlr.press/v155/yamada21a/yamada21a.pdf)

## Reading order and questions for ATOM

| Read | Question to answer in your notes |
| --- | --- |
| Introduction and Figures 1–2 | Which part of ATOM's exploration problem should planning address? |
| Sections 3.1–3.2 and Algorithm 1 | How should one policy decision map to execution duration and logged transitions? |
| Section 3.3 | How should ATOM explore both local manipulation and larger moves? |
| Sections 3.4–3.5 | Which assumptions require explicit replacement in our camera-only system? |
| Experiments and ablations | Which comparison would actually support our architecture choice? |
| Appendix | Which failure cases should become repository regression tests? |

For every answer, write one implementation consequence and one falsifiable
test. Preserve the distinction between a method's mechanics, the authors'
results, and hypotheses about the ATOM arm.

## Clarifying the previous recommendation

The proposed ATOM baseline uses a supervisor to hand control between planned
travel and learned local manipulation. That is a stage-based engineering
design. MoPA-RL instead selects direct execution or planning through action
magnitude. A later ATOM comparison could investigate that mechanism after
calibrated planner arrivals and local manipulation work. [Paper](https://proceedings.mlr.press/v155/yamada21a.html)

Also distinguish residual control, which combines a conventional command with
a learned adjustment. Johannink et al. study that approach for robot control.
An ATOM experiment must declare whether it uses an additive correction, stage
handoff or planner-augmented actions. [Residual RL paper](https://arxiv.org/abs/1812.03201)

## Prerequisites to review

Study forward/inverse kinematics and coordinate frames, configuration-space
collision checking, sampling-based planning, Markov and partially observed
decision processes, discounted returns, policy gradients, actor/critic
optimization, on-policy versus off-policy data, and experimental design.
For ATOM, add projective geometry, camera calibration, homography, temporal
tracking and the difference between measured state and commanded estimates.

Use the [P038 pipeline walkthrough](P038-pipeline-walkthrough.md) to connect
those concepts to concrete image acquisition, native module calls, observation
construction, PPO updates and saved artifacts. The autonomous environment
changes action/observation semantics and has its own README and version record.

## An original experiment worksheet

Write the chosen object, task, camera and calibration revision, geometry,
collision profile, source/destination and initial-condition distribution.
Declare which variables come from images, task context, host history and
simulator-only evaluation. Mark missing observations explicitly.

For each architecture, count accepted/rejected proposals, actual motion,
grip, stable lift, placement, non-target contact, displacement, toppling and
recovery. Report both task outcomes and compute cost. Keep evaluation seeds
and a final test set separate from training and tuning. Compare the same
physical problem and success criterion, including negative results.

Questions specific to the prototype are whether a valid random starting pose
can be reached from park, whether the full gripper fits the approach, whether
the actor can visually localize the piece under occlusion, and whether a
verified simulated hold has an available hardware observation equivalent.
These questions determine readiness for planner-assisted training.
