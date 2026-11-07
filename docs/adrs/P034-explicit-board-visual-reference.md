# P034 — Explicit visual reference for the board

Date: 2026-11-06. Status: implemented and evaluated in simulation.

## Context
P033 established that occupied-board pattern detection has insufficient coverage.
The user explicitly requested resolving blockers rather than stopping at reports.
OpenCV 4.12 installed here includes the ArUco detector. Physical marker layout has
not been measured; simulation reference layouts must be labeled experimental.

## Decision
Add a reusable acvision reference detector using four explicitly identified ArUco
markers and a supplied mapping of each marker's four corners into rectified board
coordinates. This mapping is configuration, not a simulator pose observation.
Require all configured IDs uniquely in every accepted image; never silently reuse
an old H. Fit correspondences, record reprojection residual and reject invalid
layouts. Chess orientation is supplied by the reference layout, not guessed from
checker color. Do not enable hardware calibration or claim physical accuracy.

## Alternatives and consequences
Unverified cached H hides camera/board motion. Ground-truth corners bypass vision.
Both are rejected. Markers require visible reference areas and eventual physical
installation measurements. The image detector is reusable for simulation and a
real camera; simulation integration and visual verification remain required tests.

## Approved physical-reference workflow
The user approved four printed markers and requires an installation guide. Keep
MOVE(source,target) independent from initial piece identity/layout: marker geometry
establishes squares, while current piece observations establish the grasp point.
A square address must never be inferred from a pawn's starting position.

Use DICT_4X4_50 IDs 0/1/2/3 at the a8/h8/h1/a1 outer corners, respectively.
Provide printable marker images and an explicit experimental layout for the
current 280mm simulated board. Actual board dimensions/mount coordinates must be
measured and configured; the example is not a physical calibration. Markers are
coplanar with the square surface, rigidly attached, outside the playable area.
No fallback to checker or cached H when a required marker disappears.

## Measured simulation outcome
The user approved markers. The tested layout v4 is asymmetric to clear the column; see the installation guide for exact coordinates, print sizes and units. Subpixel refinement and a 1920x1440 camera yielded 24/27 accepted frames, all with 64/64 correct square assignments, independently of the three tested piece arrangements. Three reprojection rejections remain explicit. No physical calibration or grasp-point localization is claimed.

## Implementation explanation

See [the homography walkthrough](../camera-rl/homography-explained.md) for the 16-corner fit, canonical coordinates, residual checks and piece-localization limits.
