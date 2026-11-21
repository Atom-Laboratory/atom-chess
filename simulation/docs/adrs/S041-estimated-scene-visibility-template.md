# S041 — Compare synthetic visibility against its own estimated-scene template

Status: experimental fixed-camera qualification. Date: 2026-11-20.

## Context

A lateral-entry native reach probe initialized and reached on seeds 960000/1,
but seed 960002 rejected all 256 previews. The source was localized in the real
park image; each preview used re-rendered piece positions inferred from that
image. Comparing this quantized synthetic silhouette against the original
centered template conflates re-rendering/position-estimation error with robot
occlusion. The planner must predict whether its own estimated scene is visible.

## Decision

When candidate visibility screening is requested, render an unoccluded template
from the same estimated scene at the current issued robot command. Compare each
candidate against this synthetic template, requiring near-zero apparent shift.
Both renders use the same camera, static model and camera-estimated piece XY;
neither copies live piece poses. Leave IoU, ambiguity and spatial tolerances
unchanged. Record the preview reference convention in each plan.

This template is only a planner scratch-render input. After actual execution,
the handoff still uses the real RGB frame, original camera references, sequence,
tracking and board/target-shift checks. Synthetic preview success never proves
actual arrival visibility or actor eligibility.

## Alternatives and consequences

Disabling visibility checks or lowering silhouette thresholds would conceal
occlusion and is rejected. Moving the camera changes the experiment and is not
required. This correction removes one inconsistent comparison, but incomplete
candidate search or poor real images can still reject a reset. Preserve those
failures rather than fabricating success or silently resampling evaluation seeds.
