# P033 — Evidence-based board geometry

Date: 2026-11-06. Status: accepted for the next perception increment.

## Context
P032 demonstrated graveyard rectangles incorrectly accepted as boards and biased
corners. Its complete bridge does not establish reliable perception. The user
has authorized progressing through the remaining phases without repeated prompts.

## Decision
Require an actual 7x7 chessboard pattern for automatic board geometry. Remove the
largest-quadrilateral fallback: rectangular shape alone is insufficient evidence.
Fit the 49 internal grid points to a projective transform and extrapolate the
four outer boundaries using grid coordinates 0..8, rather than linear image
vectors and the unexplained 0.8 multiplier. Preserve an ordered perimeter without
claiming chess orientation. Keep no-detection as unknown, never use oracle corners.

## Alternatives
Keeping a contour fallback with only size/aspect checks cannot distinguish a
board from the graveyard. Supplying simulator corners as detections is rejected.
Markers or explicit image-based setup calibration may be needed for occupied
boards, but must have a separate measured persistence/visibility contract.

## Consequences
Recall may decrease under occlusion; explicit failure is preferable to a false
metric frame. Test perspective/rotation/negative scenes and rerun real rendered
images before advancing. Geometric success alone cannot validate occupancy,
orientation, gripper localization or the conventional manipulation baseline.
No existing training/checkpoint, hardware flow or physical state is changed.

## Follow-up measurement contract
Evaluate the current initial scene across provisional azimuth perturbations as
well as elevations. Ground-truth initial-square/color metadata is allowed only
inside the independent evaluator to build confusion counts. Compare raw classifier
candidates, never overwrite unknown physical occupancy. Record missing detections
separately and preserve the D4 oracle-alignment caveat. This adds validation only,
not a new perception source or permission to train.
