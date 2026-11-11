# S023 — A shared object-conditioned autonomous policy

## Context

The previous residual and autonomous pilots have not qualified manipulation.
Six exported geometric kinds and 32 physical identities are available. Their
visual meshes differ from experimental contact proxies. Separate final models
for every identity would duplicate representations and complicate deployment.
The requested platform needs progressive individual experiments, combined
learning and independently measurable retention.

## Decision

Use one visual encoder and task/object-conditioned manipulation policy with
an independent safety supervisor. Logical kind/color may come from Chess
Core context. Pose estimates must come from images and calibrated host
geometry/command history. Simulator poses and contacts are reserved for
reward, safety and independent evaluation. Track individual object evidence
before balanced joint learning and compare specialists only as baselines.

Keep the existing residual experiments as historical comparison groups.
Use PPO for the first controlled environment comparison. Benchmark SAC or
recurrent PPO only against a declared limitation and fixed evaluation task.
Treat a new actor schema as a new model version. Weight transfer must verify
semantics, spaces and archive identity and record a fresh optimizer when used.

## Alternatives

Independent policies discard the explicit shared-model research question.
Unconditioned RGB makes task ambiguity and visual class uncertainty harder
to inspect. Copying hidden object state into observations breaks the camera
deployment contract. Averaging independently trained checkpoints has no
established justification for this experiment.

## Consequences

Every object needs held-out approach, grasp and lift measurements and a
documented perception/geometry qualification. Combined training must reevaluate
old objects and expose sample balance and forgetting. Algorithm selection,
CUDA efficiency and physical validity need separate measurements. The
[audit and staged gates](../../../docs/camera-rl/autonomous-multi-object-audit.md)
record the starting evidence and implementation sequence.
