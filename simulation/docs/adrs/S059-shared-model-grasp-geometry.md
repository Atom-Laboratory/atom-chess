# S059 — Share grasp geometry without a rendering dependency

**Status:** Accepted

**Date:** 2026-11-21

**Decision owners:** Simulation architecture, manipulation optimization

**Related experiments:** EXP-0006

**Related findings:** RF-0001

**Supersedes:** Example-owned shared grasp geometry implementation

### 1. Context

The first CEM launch stopped before any candidate simulation: it imported the
example diagnostic solely for its geometry/preload function, which also imported
Pillow for camera screenshots. The isolated GPU environment intentionally does
not need rendering for command generation or physics search.

### 2. Evidence

The preserved failure is `ModuleNotFoundError: PIL`. The required function uses
only NumPy, MuJoCo and the existing static aperture helper, not image data or
camera rendering. Duplicating it would create two physical assumptions to maintain.

### 3. Decision

Move the unchanged model-derived grasp geometry/preload function into the
`atom_mujoco` core package. Import it from both the visual diagnostic and CEM.
Keep screenshot generation in the example and keep the GPU environment free of
an unnecessary Pillow dependency. No physical defaults, formulas or actuator
limits change in this extraction.

### 4. Alternatives considered

Installing Pillow would mask the module boundary problem. Copying the function
would make future force/geometry fixes inconsistent. Importing private example
code also complicates immutable source snapshots.

### 5. Technical rationale

Shared static physical hypotheses belong in a reusable non-rendering module;
experiment UIs and image outputs should not be dependencies of GPU optimization.

### 6. Implementation

Extract `grasp_geometry` to `atom_mujoco/grasp_geometry.py` and replace both
callers' definitions/imports. Preserve exact function source during the move.

### 7. Consequences

The failed launch remains a dependency/architecture failure, not negative grasp
evidence. Existing formulas stay experimental and hardware-uncalibrated.

### 8. Verification

Run existing geometry/local-supervisor tests and import the shared function in
the isolated environment without Pillow. Rerun CEM in a fresh directory.

### 9. Research relevance

Single-source physical assumptions reduce experimental confounding and make
headless command generation reproducible.

### 10. Report-ready summary

ATOM extracts model-derived grasp geometry into a rendering-independent shared
module after a dependency-only pilot failure. The extraction changes neither
physical parameters nor grasp-control equations.

### 11. References

- [Bounded CEM](S058-bounded-isolated-cem-grasp-pilot.md)
- [Shared implementation](../../mujoco/src/atom_mujoco/grasp_geometry.py)
