# S047 — Test upper-sphere contact at the lower pad edge

Status: experimental diagnostic; no policy admission. Date: 2026-11-21.

## Context

The full-board endpoint screen rejected the centered head/stem grasp families.
An exploratory screen used the first pad box dimension (12 mm) as its vertical
half-extent and found 50 clear endpoints among 250 candidates. Scratch forward
kinematics revealed that the compiled orientation instead places the second
dimension (6 mm) vertically. Those 50 endpoints therefore do not establish
contact at the proposed latitude and cannot qualify a grasp. This discrepancy
requires a geometry-derived diagnostic instead of axis assumptions.

## Decision

Add an opt-in spherical-head diagnostic parameter for the contact latitude.
Derive the pad's vertical half-extent from its compiled box orientation in the
commanded pose, using scratch forward kinematics rather than live body state.
Use the camera-estimated source XY and the existing static experimental piece
geometry. The effective sphere radius is r*sqrt(1-f*f); the pad center is above
the head center by its vertical half-extent plus f*r. Preserve the default
equatorial diagnostic when the parameter is absent.

Account for the downward component of the upper-sphere contact normal. The
idealized vertical capacity per unit normal force is mu*sqrt(1-f*f)-f. Reject
nonpositive capacity, insufficient compiled force or finger travel. This static
Coulomb/servo estimate only proposes a test; measured simulated contacts and
lift feedback determine its outcome. Model dimensions and friction remain
experimental, without a hardware or CAD-accuracy claim.

Bound the horizontal finger preload by N*(sqrt(1-f*f)+mu*f), including the
horizontal friction component, rather than treating actuator force as the tilted
contact normal. The opt-in diagnostic aligns the wrist and centers above the
source before descending. Its lift target is at least 1.5 piece heights above
the pick TCP (still subject to the declared envelope and all sweeps); success
requires a measured rise of one piece height, without lowering that criterion.

## Alternatives

Disabling the gripper hulls or removing neighbors would change the crowded
problem. Continuing reach-only PPO cannot demonstrate a grasp. A broad learned
contact workspace remains unavailable until an executable baseline is measured.

## Consequences

Keep full-path and per-step sweeps, runtime contact/topple checks, tracking,
fresh camera reference and fail-closed recovery. Save the exact geometry and
force assumptions with the result. No RL lease or visual grasp/lift qualification
is granted by the endpoint screen or this deterministic experiment.
