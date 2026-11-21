# S045 — Revalidate the last verified entry before repeating the full search

Status: experimental performance optimization. Date: 2026-11-20.

## Context

Populated-board corridor screening can evaluate many rejected entry/wrist/branch
combinations on every reset, dominating rollout time. The scene has a fixed task
and camera, with new RGB-estimated positions and bounded placement jitter.

## Decision

Opt in to remembering only the parameter tuple of the last verified arrival:
height index, configured lateral offset, wrist angle and elbow branch. Try that
tuple first in the next bounded candidate family, without adding candidates or
reusing any path, pose estimate, collision verdict or camera evidence. Rebuild
all IK, previews, corridors, approach/retreat and live checks for the new scene.
Store no learned-policy inputs or privileged piece coordinates in this preference.

## Alternatives and consequences

Caching a trajectory or acceptance verdict would be unsafe after a piece moves.
Repeated exhaustive search is correct but slow. Candidate ordering preserves
the same budget and validity requirements; an invalid preference falls back to
the original ordering. The selected candidate and preference are logged so the
changed reset distribution is visible. This is a planner heuristic, not an RL
weight update or evidence of generalization to another board/camera/task.
