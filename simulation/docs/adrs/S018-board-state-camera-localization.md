# S018 — Localize pieces from camera and logical board state

## Context

ACVision rectifies RGB using board markers and reports square candidates. The
P038 planner previously descended at the nominal square center. The board
state identifies the intended piece, but its exact location must be observed.

## Decision

Use the logical FEN to identify expected occupied squares. Register the
rectified RGB against a centered calibration to estimate board-relative piece
offsets. Require visual evidence at the source and never substitute the live
simulation pose. Use simulated contact, toppling and non-target displacement
only as training supervision. Penalize new peaks in displacement beyond the
noise tolerance. Keep model geometry as static motion calibration and create synthetic
calibration RGB independently of the live episode.

## Alternatives

Nominal square centers cannot account for placement variation. Live simulator
poses are unavailable to the physical robot.

## Consequences

The estimate depends on camera orientation, appearance calibration and
visibility. Occluded or ambiguous offsets are unknown. A real installation
requires images from its camera and calibration against the robot base.
