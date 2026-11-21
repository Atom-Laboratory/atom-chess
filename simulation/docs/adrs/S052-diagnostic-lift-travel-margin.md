# S052 — Declare diagnostic lift travel independently of the success threshold

Status: experimental deterministic diagnostic. Date: 2026-11-21.

## Context

After the partial-contact closure fix, elliptic/10 maintained the isolated pawn
grasp throughout its lift. Measured rise was 31.419 mm against the unchanged
32 mm requirement, so the result correctly remained `LIFT_NOT_CONFIRMED`. The
old target was the approach height: only 33.940 mm above the pick TCP, leaving
little room for contact compliance/slip. Endpoint travel and verified piece
rise are distinct quantities.

## Decision

Add an explicit optional diagnostic lift travel in multiples of the compiled
selected-piece collider height. Use the greater of that requested target and
the original approach height, still inside the existing envelope, joint limits,
whole-path screen and per-step/runtime checks. Record the option and actual
target with provenance. Compare 1.5 heights while preserving the required
measured rise of one complete piece height, sustained contact and settled
feedback. Default behavior retains the historical endpoint when absent.

## Alternatives and consequences

Reducing the required rise or relabeling the 31.419 mm trial would hide its
failure. Explicit additional travel instead tests the same success condition
with a different, documented target. Collider height is experimental model
geometry, not a new claimed physical measurement. Positive isolated results
remain separate from crowded entry, camera outcome verification, transfer,
policy qualification and hardware readiness.
