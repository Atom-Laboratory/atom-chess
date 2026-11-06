# P037 — Native camera-to-policy runtime

## Implemented path

MuJoCo RGB frame -> persistent acvision C ABI -> native reference detection and
rectification -> immutable camera observation -> task-conditioned actor features.

The native adapter links the existing BoardDetector, Homography, PieceDetector,
ArUco reference detector and optional P035 foreground diagnostic. Python uses
ctypes and passes only contiguous uint8 RGB plus explicit layout configuration.
The library stays loaded across frames and has one independent context per
worker. Processing writes directly into memory. The older file executable and
VisualGraspEnv remain available.

The old VisualGraspEnv v3 initializes its robot pose using the actual simulated
piece position and centers its camera using the piece origin. P037's preview
uses an explicitly configured initial arm pose and camera, with source/target
provided by the caller. Future RL environments must use this observable boundary
instead of copying v3 reset.

## Build and exercise

Run in PowerShell from the repository root.

~~~powershell
cmake -S software/acvision -B build/p037-native -G 'Visual Studio 18 2026' -A x64 -DOpenCV_DIR=D:/opencv/build/x64/vc16/lib -DBUILD_TESTING=OFF -DACVISION_NATIVE_RUNTIME=ON
cmake --build build/p037-native --config Release --target acvision_runtime

$run = Join-Path simulation/mujoco/runs ('native-policy-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/preview_native_policy.py --scene simulation/mujoco/runs/p035-steep-relayout/reference-scene.xml --layout docs/camera-rl/evidence-p035/high-camera-layout.json --library build/p037-native/bin/Release/acvision_runtime.dll --output $run --frames 100 --empty-fixture --preview
~~~

The scene path is an existing P035 marker-scene artifact. It uses the high-camera
layout and absolute mesh/texture paths, so the underlying assets must remain
available. The initial observation pose is [-1.5,.12,-1.5,0,0] in the existing
five-joint order (rad,m,rad,m,m). The fixed camera looks at [.245,0,.012] m,
distance 1.05 m, azimuth 270 degrees, elevation -75 degrees, 1920x1440 px.

The preview shows raw camera and rectified RGB. It captures frames from a fixed
initial scene. It does not execute actions. Its initial pose is an experimental
setup, rather than a verified collision-free motion from another pose.
The optional empty fixture temporarily hides free chess-piece bodies during
background acquisition, then restores their positions before current capture.
Only the resulting RGB frame enters native perception. This models a synthetic
empty-board calibration capture, and requires a real empty-board RGB capture
for a physical camera.

## Runtime interface

NativeVision(library, layout=..., camera_id=...) owns a C++ context.
observe(rgb,captured_at_s=...) returns native geometry, candidate labels,
rectified RGB, provenance and a monotonic-clock capture timestamp.
set_empty(rgb) registers an explicitly supplied background. Missing references
in that background invalidate its previous registration.
close() is idempotent. Context calls are serialized within the Python adapter.

The C ABI checks version and structure size. Callers supply an exact contiguous
RGB buffer and an 800x800x3 output buffer. Missing geometry returns a cleared
rectification and unknown (-1) candidate labels. Geometry is recomputed for each
frame. C++ exceptions are converted into error codes and messages.

The context has no simulator pointer or task/reward argument. Native and actor
arrays use immutable byte backing. Multiple workers require separate contexts.
The adapter supports one input image at a time. It is currently an in-process
bridge, so a hard native crash would also terminate its Python worker.

## Actor inputs and explicit unknowns

policy_observation accepts a CameraObservation plus source, target, previous
normalized action, commanded joint targets and phase. It checks the reference
orientation and capture age. Missing, stale or future geometry raises an explicit
error. The default .25 s age budget and preview's 1 s budget are experimental
runtime settings.

The returned features contain only the following values.

| Field | Shape and meaning |
|---|---|
| image | uint8 CHW 3x96x96, resized native-rectified RGB |
| task | float32 [source file,row,target file,row] divided by 7 |
| previous_action | Four normalized commanded residuals |
| commanded_joints | Five host command targets in existing SI joint order |
| phase | One integer index for OBSERVE/APPROACH/GRASP/LIFT/TRANSPORT/PLACE/RELEASE/RETREAT |

The caller is responsible for supplying command history. Encoder readings,
body truth, contacts, reward and diagnostics have no actor-input parameter.
Experimental foreground centroids remain diagnostic and never become a
fabricated metric grasp point. Candidate colors remain unverified occupancy.
The input images may be used by a future hybrid residual policy without requiring
a visually inferred 3D pose field.

## Measured checks

Thirty consecutive frames from the visible observation pose yielded 30 usable
task-conditioned inputs in p037-native-visible, mean native processing about
33.35 ms per frame. With explicit synthetic background calibration,
p037-native-background yielded 30/30 inputs, about 31.89 ms native processing
and 15 foreground centroids per frame. These are repeated static captures,
rather than independent camera-coverage trials. Timings exclude MuJoCo rendering,
Python immutable-array copies, policy inference and physics.

A 15-pose diagnostic found 11 poses with accepted reference geometry at the
fixed high camera. Native reference availability alone was the selection
criterion. It did not evaluate a swept trajectory or full piece visibility.
Raw rejected attempts remain preserved in p037-native-preview and
p037-native-folded. All attempts use fresh directories.

Tests exercise exact parity of H, candidate labels and rectified pixels against
the native CLI, RGB integrity, visibility loss and recovery, stale/future input,
background invalidation, context independence, direct ABI buffer failure,
immutable outputs and exclusion of privileged actor fields.

## Remaining gates for training

The software now has an observable task-conditioned camera input and a persistent
native processing path. Full camera-guided training still requires the following.

1. Qualified current-piece localization or a justified image-based local control
   baseline, including source grasp offset and height/parallax handling.
2. Calibrated board-to-base mapping and explicit experimental TCP/aperture profile
   in simulation, then measured hardware equivalents.
3. A deterministic generic transfer baseline using the real acmotion task/planner
   interfaces with swept collision checks, capture removal and graveyard tasks.
4. Multi-frame visual confirmation of grasp, lift, stable placement and release.
5. A new Gym environment with separate actor observation and simulator reward
   boundaries, then bounded residual actions and a gated training launcher.

The P037 actor schema is a building block for that environment. Training-ready
remains false in the preview report because these manipulation gates remain open.
See [ADR P037](../adrs/P037-native-camera-policy-boundary.md).
