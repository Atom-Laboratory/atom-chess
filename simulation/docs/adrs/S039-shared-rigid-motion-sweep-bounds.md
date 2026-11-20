# S039 — Cancel shared rigid motion in nominal distance bounds

Status: accepted for the nominal compiled-model preflight. Date: 2026-11-20.

## Context

The fixed-camera M2 approach study rejected visible candidates because the
initial joint box could not be certified. A numerical probe of recorded seed 7
found a clear endpoint and an unresolved box at scale 1/128, but certification
at 1/1024. The bound adds absolute motion of both geometries even for a joint
that rigidly translates or rotates both shapes together. Such a common transform
leaves their pair distance invariant. Smaller boxes alone hide this inefficiency.

## Decision

For nominal geometry, build a pair-specific travel bound and omit joint
components that occur in both kinematic ancestor chains. Use that same bound
for sphere pruning and exact-distance certification. Retain all relative-joint
motion, clearance, recursion and sample limits. Do not apply this cancellation
to callback-configured or externally supplied carried-object coefficients:
their common rigid-motion semantics are not established by the ancestor chains.

## Alternatives and consequences

Increasing the sample budget adds cost without fixing the overestimate. Shrinking
collision shapes or clearance changes the physical question and is rejected.
The tighter bound can certify more nominal paths without changing a contact mask
or permitting overlap. Test common rigid rotations, moving relative joints,
pruning parity and configured/held-object fallback before native replay.

This is a conservative nominal geometric check, not a dynamics proof. Reach
evaluation, visible approach admission, grasp/lift workspace qualification and
camera-only outcome verification remain separate gates. No training eligibility
flag is enabled by this change. Preserve the fixed camera and earlier reports.
