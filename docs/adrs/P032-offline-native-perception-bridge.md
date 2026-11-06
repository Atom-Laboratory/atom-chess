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
