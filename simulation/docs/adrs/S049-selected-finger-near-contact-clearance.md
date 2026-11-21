# S049 — Separate near-contact margin from forbidden penetration

Status: opt-in simulation diagnostic; default behavior unchanged. Date: 2026-11-21.

## Context

The isolated head closure at load factor 1.5 was rejected when the target-to-finger
hull distance was 0.997 mm, against a global 1 mm planning margin. No hull
penetration was reported. Lower load factors passed closure but lost contact in
lift. This couples a free-space margin to a force-limited intentional grasp.
The pad proxies may contact the selected piece; finger hull penetration and all
contacts with other pieces remain forbidden.

## Decision

Allow the swept checker to receive explicit per-pair nonnegative clearance
margins. Every unlisted pair retains the original margin. Pair-specific margins
apply to broad-phase pruning, distance thresholds and interval certificates,
including carried-object checks. They never skip distance checks.

Expose an opt-in margin only in the deterministic local diagnostic, scoped to
the selected piece versus convex hulls attached to the two moving finger bodies.
The minimum is zero: touching/penetration at or below zero is still rejected.
Other pieces, fixed gripper parts, robot self pairs and board retain their
original margin. Runtime forbidden-contact handling remains unchanged. No model
scale, geometry, contact masks, friction, gains or force limits are modified.

## Alternatives and consequences

Lowering every pair's margin would weaken unrelated clearance. Allowlisting whole
finger hulls would suppress actual penetration checks. This explicit near-contact
margin permits a measured preload comparison while retaining those checks. It
must appear in provenance and results. A successful diagnostic under a different
margin would not retroactively qualify the original strict-margin experiment,
grant an RL lease or establish a hardware safety margin.
