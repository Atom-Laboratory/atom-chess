# P024 — Pre-shape fingertips above crowded squares

## Context
The recorded E2–E4 transfer fails swept preflight in descend, with 0.8875 mm
between finger_1_pad and the D2 pawn base, below the existing 1 mm margin.
The planner descends with a fully open 48.1 mm jaw gap on 35 mm squares.
This is a geometric planning defect; disabling contacts or RL does not fix it.

## Decision
Compute a pregrasp aperture from the selected simulated cylindrical stem radius
and the model's fingertip geometry. Allow an experimental 3 mm gap per side.
Pre-shape at source approach height, descend at that aperture, close normally,
release at the same aperture, retreat, and fully open only above destination.
Validate every additional interval and execute the same phase order. Reject a
required aperture outside joint limits. Preserve the 1 mm collision margin and
all neighboring-piece checks. This uses experimental proxies, not CAD accuracy.

## Alternatives
Reducing collision clearance or omitting neighbors would conceal the defect.
Widening square spacing changes the configured board. Both were rejected.
A general grasp orientation search remains future work for blocked layouts.

## Consequences
Some crowded descents may become feasible; success still requires swept
preflight and runtime grasp/lift/release feedback. No generic manipulation or
hardware safety claim follows from this change.

The grasp command also targets the proxy stem diameter with 0.5 mm compression
per side instead of the mechanical lower stop. The old lower-stop target made
the nominal fingertips approach each other inside the clearance margin. These
compression and aperture allowances are experimental, not force calibration.

## Validation
The original visual bundle E2–E4 passed 318 swept samples and completed with
bilateral grasp and release feedback, no unexpected runtime contacts, and one
confirmed-state revision. Regression repeats with identical physical proxies
and lightweight visuals, then reproduces the old D2 collision with full-open
descent. Other layouts and pieces may still be rejected.
