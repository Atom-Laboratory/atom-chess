# P032 — Offline native perception bridge

Date: 2026-11-05. Status: accepted for Phase B1 after user approval of P031.

## Context
P031 requires actual acvision processing before a new training environment. Current
library takes BGR cv::Mat images but exposes neither a machine-readable executable
nor confidence, orientation, or calibration validity. The detector can mistake a
large rectangle for the board. Preserve that limitation explicitly.

## Decision
Add an offline image executable linked to the existing acvision library. Detect
corners, call actual Homography and PieceDetector, export JSON plus raw-corner and
rectified-grid overlays. Output is diagnostic/unvalidated and must never authorize
motion. All cells have unknown reliability; no invented confidence or gripper pose.
Image grid indices are not chess addresses until orientation is established.
Reject invalid images and geometrically degenerate corners; preserve existing
output directories. Do not accept simulator-provided corners as vision detections.

Render an experimental fixed lateral camera with MuJoCo into a fresh directory.
A separate evaluator may project simulator square centers to measure detector
mapping error; those truth coordinates never enter the native perception bridge.
No undistortion is claimed for input without calibrated optics. Simulation images
are ideal pinhole captures; hardware calibration remains required.

## Alternatives
Python duplicate detection is rejected. Bindings and persistent transport remain
later throughput work; PNG/executable overhead is acceptable only for offline
validation. Do not fix detector algorithms in the same integration commit.

## Consequences
A successful process exit means processing completed, not reliable perception.
Explicit status and missing fields keep training gated. Measure current failures
before a separate corner/orientation implementation. No PPO run, environment
replacement, physical state update or hardware dispatch belongs to this increment.

## B1 acceptance-contract completion (2026-11-05)

Inspection of c005ccd found gaps against the approved detailed B1 requirements:
IMREAD_COLOR silently accepted unsupported input channels/depths; JSON lacked
input/configuration/build identity, structured errors and explicit completion;
tests did not compare direct library calls or exercise the requested negative
images and degenerate corners. These are integration gaps, not authorization to
change BoardDetector, Homography or PieceDetector algorithms.

Revise the offline output to schema 2. Validate decoded 8-bit, three-channel BGR
input without automatic conversion. The only supported configuration is the named
built-in defaults profile; reject other configuration IDs rather than silently
falling back. Share small validation/orchestration helpers with native tests;
keep all perception algorithms in their existing classes. Add provenance and
complete/error flags, including diagnostics for rejected input when an output
directory can be reserved. Preserve partial artifacts on I/O failure, never mark
an unsuccessful export as completed. Tests must record rectangle false positives
as limitations, not assert that the unchanged detector rejects them.

Homography is unequivocally original decoded image pixels -> rectified pixels:
compute maps ordered TL/TR/BR/BL input corners to (0,0),(800,0),(800,800),(0,800).
warp uses the original decoded image, not detector-internal grayscale/blur output.
The 800 endpoint is a continuous rectangle boundary; raster indices are 0..799.
This is not a board-to-base transform, optical calibration, or chess orientation.

No algorithm fixes, hardware commands, physical-state updates or learning belong
to this completion. The user subsequently explicitly authorized committing the
verified diff. No push is authorized.
