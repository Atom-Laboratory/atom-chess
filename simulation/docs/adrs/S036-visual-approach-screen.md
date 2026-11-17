# S036 — Screen approach endpoints for target visibility

## Context

M1 executed four collision-checked approaches but could not localize e2 at
arrival. The fixed camera's board registration was still valid.

## Decision

In an opt-in experiment, screen the existing native approach candidates
with the same camera and RGB localizer. Render candidate commands on a
scratch scene constructed from visually estimated occupancy. Keep all
geometric and live safety checks and independently reacquire RGB at arrival.

## Alternatives

A stale pre-approach estimate cannot verify arrival visibility. Moving the
camera would change the experimental configuration.

## Consequences

This compares one planner selection criterion while holding geometry and
training settings fixed. A visible approach does not qualify descent or lift.
