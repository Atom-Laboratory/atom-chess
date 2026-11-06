# P035 — Image evidence for current piece location

## Context

P034 locates the board plane from four ArUco markers. It leaves piece position
unknown. A camera mounted to the side views raised piece surfaces at a different
angle from the board plane. A silhouette centroid rectified with the board
homography can therefore have a systematic offset from the actual piece axis.

## Decision

Add an opt-in diagnostic to the native acvision image adapter. Capture a
reference image of the empty board with the same camera, lighting and robot
pose. Register both frames independently from the same configured ArUco layout.
Subtract the registered images and retain only isolated foreground components
contained in one square. Report their centroids as projected image evidence
and show them on the rectified overlay. Keep piece_center and motion_ready
unchanged until a calibrated estimator can justify a physical grasp point.
Treat missing evidence as unknown.

Evaluate the candidate against independently measured scene piece positions.
The native estimator receives RGB, an empty-board RGB reference and layout.
The evaluation alone may read MuJoCo state.

## Alternatives

Per-square edge density cannot localize a piece and can mistake a neighbor
for the source piece. Simulator object labels and depth would simplify the
measurement but would bypass the RGB perception interface. Pose fitting with
camera intrinsics and known piece geometry is a later option if the projected
silhouette is too biased.

## Consequences

The reference frame must be refreshed after changes in illumination, optics or
background. Shadows, partial occlusions, foreground spanning several cells and
parallax can make the diagnostic fail or bias its result. The diagnostic does
not classify pieces, resolve occlusion or authorize a robot move.

## Validation

The [developer guide](../camera-rl/p035-piece-localization.md) records three
36-frame sweeps. The lateral configuration matched 5 of 594 expected piece
observations. Moving one marker for the higher camera raised this to 147 of
594. The capture pose and estimator need further qualification before an
observed position can feed acmotion.
