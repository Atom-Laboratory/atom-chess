# S016 — Elevated wrist alignment and fixed camera-only qualification

## Context

The dense d4 neighbor is displaced during descent by a finger collision hull.
Changing wrist targets while lowering can create that contact even when a
final orientation would provide clearance. Repeated fixed-scene evaluations
also do not establish a 90% success rate under placement variation.

## Decision

Select a wrist residual during the elevated approach, hold it through descent
and grasp, and require angular alignment before leaving the elevated phase.
Permit a new orientation decision during elevated transport. Rate-limit both
decisions. Add bounded setup-only XY placement variation, sampled from the
episode RNG. Dynamic ground truth never supplies actor observations or reward.

Qualification uses a recorded set of 30 seeds, requiring target appearance
confirmation and unchanged neighbor camera evidence. Capture before/after
images, configurations, source identities and all failures. The 90% threshold
applies to this declared simulation test set.

## Consequences

A privileged diagnostic may identify simulated contact geometry, but is kept
outside policy input, reward and qualification success. Full-board, arbitrary
piece and hardware qualification remain separate. Camera appearance evidence
must not be described as proof of all physical contact or transient motion.

## Appearance and placement criteria

Generate upright camera references across sixteen yaw orientations. Reject
empty and fallen-piece reference fixtures. Remove disconnected foreground
speckles smaller than four pixels before contour comparison. Keep the IoU
threshold at 0.65. A translation match is allowed only within the margin in
which the modeled circular base fits inside its board square.

This processing addresses white-on-white rendering and raster edge variation.
It is an experimental appearance check and must be validated independently
from simulation task state. Initial placement variation is bounded to 1 mm
in each horizontal direction for the declared qualification fixture.

The selected nominal source and destination wrist orientations (72 and 164
degrees in this fixture) came from static clearance diagnostics. The policy
learns residual corrections around those nominal orientations. These values
are fixture configuration, not a claim of a generally learned motion plan.
