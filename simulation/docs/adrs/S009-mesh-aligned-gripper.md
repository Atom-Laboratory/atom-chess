# S009 — Align finger travel with exported gripper geometry

Date: 2026-11-04. Status: accepted. Replaces v5 global-Z finger travel.

## Evidence and cause

The two finger STL meshes share dominant planar normals approximately
[0.79539,0,0.60609]. Their orthogonal rail direction in the X/Z assembly plane
is [-0.60609,0,0.79539]. The former global Z slides deviated about 37 degrees
from this direction, moving the fingers sideways off their guides.
Fingertip projections indicate an approximately 48.096 mm inner-face gap at
the exported reference pose. Existing pad positions did not follow these faces.
The reproducible inspect_gripper_geometry.py script reports mesh hashes,
area-weighted face normals and projected fingertip bounds in millimetres.

## Decision

Use opposite mesh-aligned axes, with equal coupled displacement. Orient and
position pad boxes against the projected inner fingertip faces. Keep the opening
midpoint stationary. Opening is zero displacement; closing is -0.021 m per
finger, leaving approximately 6.096 mm between mesh faces and 3.096 mm between
the synthetic 1.5 mm thick pads. This conservative software stroke is a modeling
choice, not an extracted servo limit. Controls read endpoints from the manifest.
Generate a new interactive-chess-v6 bundle and interactive-gravity-v3 profile.

## Limits

This corrects travel geometry from the exported meshes. It does not reconstruct
the Fusion servo crank, passive links or nonlinear angle/opening relationship.
The previously observed -45 to +10 degree joint limits are not applied to slides.
No physical calibration is claimed. Fusion inspection was interrupted by the
user; this revision relies on mesh analysis, not a completed Fusion joint audit.

## Verification

Regression checks independently inspect triangle normals, verify travel against
those normals at two arm poses, preserve pad orientation and opening midpoint,
and retain the physical pawn close/lift/release test. Old bundles are preserved.
