# P036 — Experimental qualification of camera geometry and piece perception

Status — first delivery implemented and measured. No commit or push performed.

## Initial repository audit and inspected interfaces

The initial branch was ros2_simulation, HEAD dcf2dc1. Recent commits covered
P033 pattern correction, P034 references, P035 foreground evidence and guides.
Modified chess_commands.py and playground.py and all pre-existing untracked
monitor, CAD, training and attempt directories were preserved.
The complete initial Git status and identities are in
[evidence-p036/audit-before.json](evidence-p036/audit-before.json).

Inspected ADRs P031–P035, docs/camera-rl, both capture scripts, archived P033
captures/report, layout v4, native bridge, BoardDetector, Homography,
PieceDetector, reference detector, native tests, Python tests and CMake build.
The audit inventory records the documentation versions and 232 protected inputs.

| Capability | Audited state |
|---|---|
| Checker 7x7 detection | Implemented, native synthetic rotation/perspective tests pass, succeeds on 11/27 paired occupied/empty fixtures |
| Projective boundary | Implemented, 49 grid intersections fit and outer boundary extrapolated |
| ArUco layout v4 | Implemented when explicitly selected, four IDs 0–3, 16 black-pattern corners, experimental dimensions |
| Subpixel | Implemented and hardcoded CORNER_REFINE_SUBPIX in board_reference.hpp |
| Native schema | Schema 2, original decoded pixels to 800x800 rectified pixels, orientation explicit, physical readiness false |
| Camera controls | P033 CLI azimuths only. P034 CLI elevations/layout. Resolution, distance and remaining angles are hardcoded |
| Evaluator isolation | Ground truth used in projected-point/error evaluation, never in native detector arguments |
| Foreground centers | P035 experimental diagnostic, low coverage, unqualified grasp position |
| Resolution/refinement sweeps | Specified, require configurable capture/native settings |
| Multicamera, ChArUco, physical calibration, qualified 3D grasp | Pending |

The current layout really is v4. Its SHA256 is
f43edd499846a4db6c1f815b19812fb94f1895a65dedae6979ed8ce1a9051274.
The model SHA256 is
2b439e465a9f048ed49df4d681a965650a5a1347f728c2b04cba9c4a935b6b59.
Geometry and physical assets were preserved.

## First delivery implementation

- Added an opt-in --save-evaluator export to validate_board_reference.py.
  It saves independent 64-square surface projections, canonical named centers,
  image identity, camera parameters and current color truth after native execution.
  Existing capture behavior and native algorithms are preserved.
- Added qualify_saved_perception.py for same-file checker/ArUco comparison,
  exclusive directories, configuration manifests, dependency hashes, replay,
  per-frame statuses, observation/overlay identities and subprocess latency.
- Added compare_perception_reproductions.py to compare historical/current images,
  numeric records, runtime identities and protected file integrity.
- Added test_perception_qualification.py for manifest integrity, replay inputs,
  duplicate/unsafe IDs, immutable output, detector argument isolation, image
  matching, rejection denominators, evaluation isolation, orientation separation
  and deterministic report construction.
- Added ADR P036 and this protocol. Existing algorithms remain byte-identical.

Every paired observation identifies its source image, executable, native source
hash, OpenCV version, layout, model dependencies, evaluator input and output
artifacts. Replay verifies identities before and after execution. A start
manifest remains immutable. completion.json is the successful terminal record.
A partial run without completion.json requires inspection and a fresh output
directory for retry.

## Experimental and evaluation conventions

Native input is RGB-file content decoded by OpenCV into BGR, plus explicit
configuration. Native command lines contain image, new output and optional
reference layout. Evaluator truth files are never native command arguments.
Python reuses the existing evaluator, rather than implementing perception.

For both methods, geometric diagnostics use the same best D4 alignment in the
independent evaluator. This is explicitly oracle-aligned geometry. Chess-square
addressing is separately scored against configured a8 orientation. Checker
orientation is unknown. Unknown addresses stay in the 64 x frame denominators.

The matrix maps original decoded image pixels to rectified pixels.
Ordered outer boundary TL/TR/BR/BL maps to (0,0),(800,0),(800,800),(0,800).
Image pixels, rectified pixels, grid indices, square names, board metric XY and
robot-base XY remain separate coordinate systems.

An accepted frame has completed native processing and finite available H.
It remains an unvalidated candidate. Residual is available for accepted
reference fits only. Checker fit residual and rejected reference-fit residual
are absent from the native contract. The combined reference failure warning
does not identify the precise failure subtype.

False-acceptance rate, physical grasp error and CPU use remain unavailable.
False acceptance needs independently declared validity labels and mechanical
error budgets. Confirmed occupancy remains unknown. Candidate-color confusion
is available per accepted geometry frame under the stated oracle alignment.
P035 foreground localization is outside this first paired capture configuration.

Latency is one external executable invocation including startup, decoding,
processing and overlay export. Mean, median, p95 and effective sequential FPS
are reported. This is an offline end-to-end measurement with fixed checker-first
ordering, without warmup or isolated CPU benchmarking. It cannot establish
persistent-loop or training throughput.

## Historical reproduction results

| Protocol | Frames | Accepted | Rejected | Numeric records matching archive | Identical PNG hashes |
|---|---:|---:|---:|---:|---:|
| P033 | 9 | 2 | 7 | 9/9 | 6/9 |
| P034 | 27 | 24 | 3 | 27/27 | 5/27 |

P033 retained 800x600, lookat [0.245,0,0.012] m, radial distance .85 m,
azimuths 265/270/275, elevations -35/-45/-55 and vertical FOV 45 degrees.
Its accepted views retain 64/64 oracle-aligned assignments.

P034 retained 1920x1440, distance 1.05 m, layout v4, the same angular sweep,
initial/empty/offset arrangements and the capture script's existing Z=.12
robot joint setting. Accepted frames retain 64/64 directly named assignments.
P033 and P034 robot observation poses/capture initialization follow their
respective historical scripts. Historical totals therefore are separate
reproductions, rather than a controlled causal comparison.

MuJoCo remains 3.17.0. Current Python dependencies include NumPy 2.5.4 and
Pillow 12.3.0. Native OpenCV is 4.12.0. Current executable SHA256 is
f035ad0995190fdd9c8afa730c4f817dba440da9217fd9af34387a97894736b7.
It differs from both historical executables because the bridge evolved.
The model and layout hashes match. Historical Python/graphics runtime identity
is incomplete, so the exact rendering-difference cause remains unresolved.

Decoded pixel comparison finds 26 differing pixels total across P033 and
6058 across P034, each with maximum channel difference 1. These differences
do not change the compared numeric results. Historical per-frame latency was
unmeasured. Current paired latency is a separate measurement.

The detailed reproduction report preserves per-frame warnings, overlays, errors,
source hashes, pixel changes and archived/reproduced values.
All 232 protected input hashes matched after execution.

## Experiment 1 feasibility and paired measurements

Both native modes processed the exact same 27 image files, 54 observations.

| Arrangement | Checker accepted | ArUco accepted |
|---|---:|---:|
| Initial | 2/9 | 8/9 |
| Empty | 7/9 | 8/9 |
| Offset | 2/9 | 8/9 |
| Total | 11/27 | 24/27 |

All accepted frames assign 64/64 centers under the shared oracle-aligned geometry
convention. Across all 1728 square observations per method, checker yields
704 correct geometric assignments and 1024 unknown. ArUco yields 1536 correct
and 192 unknown. Checker provides 1728 unknown named addresses.
ArUco supplies 1536 correct named addresses and 192 unknown. It has 24 correct,
zero incorrect and three unknown frame orientations.

Accepted-frame mean error ranges are approximately 0.452–3.673 mm for checker
and 0.431–0.648 mm for ArUco, scaled by the experimental 35 mm square pitch.
These conditional error ranges must be read alongside coverage.

Mean process latency was about 716.91 ms for checker and 131.19 ms for ArUco
in paired-final. The observed speed difference includes every part of the
external process and is subject to the timing limitations above.
Replay produced identical perception/evaluation metrics for all 54 observations,
with expected timing variation. Replay is a reproducibility check, rather than
another independent sample.

Experiment 1 is technically feasible using the existing detectors.
This small ideal-camera fixture set establishes controlled comparison feasibility.
General method qualification and manipulation acceptance remain pending.

## Ten-experiment protocol

The protocols below distinguish measurements already run from planned conditions.
Proposed counts are a reproducible pilot plan, rather than a statistical power
claim. Final millimetre acceptance budgets require actual gripper, piece and
assembly measurements. No arbitrary mechanical safety threshold is introduced.

### 1 — Checker intersections versus ArUco

- **Hypothesis** — Marker reference improves accepted board geometry under occupied-board occlusion.
- **Independent variable** — Native checker versus four-marker reference.
- **Controlled variables** — Identical image bytes, camera, FOV, resolution, scene, arrangement and independent points.
- **Configuration and status** — Executed on 27 P034 recaptures at 1920x1440 and distance 1.05 m, nine poses across initial/empty/offset.
- **Input** — RGB PNG and explicit layout for reference mode.
- **Permitted ground truth** — 64 projected surface centers, loaded by evaluator after native execution.
- **Metrics** — Accepted/total, shared D4 geometry errors, named orientation separately, warnings, process latency.
- **Repetitions** — 27 distinct static fixtures, one pass per method, one replay for determinism.
- **Acceptance** — Infrastructure passes when input hashes match and metrics reproduce. Method qualification requires measured mechanical tolerance and held-out imagery.
- **Limitations** — The checker can detect the 7x7 pattern in 11/27 frames. Geometry is unknown on rejection. Accepted geometry alone cannot validate manipulation.

### 2 — Piece distribution

- **Hypothesis** — Piece distribution changes geometry availability and localization coverage.
- **Independent variable** — Empty, initial, sparse and dense midgame arrangements.
- **Controlled variables** — Fixed camera, illumination, marker layout and resolution.
- **Configuration and status** — Initial/empty/offset measured in experiment 1. Sparse/dense midgame conditions require new capture configurations.
- **Input** — Rendered RGB with recorded arrangement and seed.
- **Permitted ground truth** — Current occupancy/body positions in evaluator only.
- **Metrics** — Geometry acceptance, piece coverage, missing detections, FP/FN and unknown observations.
- **Repetitions** — Current 9 views per arrangement. Proposed additional two fixed sparse and two dense fixtures per view, one capture each.
- **Acceptance** — No occupancy acceptance claim until FP/FN and grasp clearance budgets are defined.
- **Limitations** — Current bridge confirms no occupancy and provides heuristic color candidates. P035 foreground requires an empty reference.

### 3 — Camera geometry

- **Hypothesis** — A complementary viewing direction reduces occlusion and geometric error.
- **Independent variable** — Azimuth, elevation and radial distance.
- **Controlled variables** — Detector, resolution, board and marker layout.
- **Configuration and status** — Historical nine-pose sweep reproduced. New distance sweeps require parameterization of the scripts.
- **Input** — RGB and complete free-camera parameters.
- **Permitted ground truth** — Board surface points, piece locations and graveyard bounds evaluated separately.
- **Metrics** — 64-square geometry, orientation, piece coverage, arm occlusion, graveyard visibility and latency.
- **Repetitions** — Executed 9 P033 and 27 P034 frames. Proposed 3 distances x 9 angles x 3 arrangements, 81 static captures.
- **Acceptance** — Select candidates only after coverage and physical installation constraints are established.
- **Limitations** — Radial distance is not mounting height. Graveyard visibility and occlusion segmentation metrics remain pending.

### 4 — Resolution

- **Hypothesis** — Increasing resolution reduces localization error with additional computation.
- **Independent variable** — 800x600,1280x960,1920x1440.
- **Controlled variables** — Same FOV, scene, layout, camera and illumination.
- **Configuration and status** — Historical runs changed other factors. Controlled capture resolution needs a configurable renderer.
- **Input** — Rendered RGB at each declared resolution.
- **Permitted ground truth** — Same 64 board points projected with each renderer.
- **Metrics** — Normalized planar error, detection/rejection, localization and process latency.
- **Repetitions** — Proposed 3 resolutions x 9 views x 3 arrangements, 81 captures.
- **Acceptance** — Choose a Pareto tradeoff after error/cost budgets are measured.
- **Limitations** — Historical resolution observations alone do not isolate resolution effects. Timing needs sequential isolated benchmarking.

### 5 — Subpixel refinement

- **Hypothesis** — Refinement improves corner precision on identical images.
- **Independent variable** — CORNER_REFINE_SUBPIX on/off.
- **Controlled variables** — All native parameters except the declared refinement setting.
- **Configuration and status** — Currently hardcoded on in reference detector. A separate versioned native config extension is required.
- **Input** — Same saved RGB files.
- **Permitted ground truth** — Independent board points and separately projected marker corners for corner-error measurement.
- **Metrics** — Corner error, fitted residual, independent errors, latency and temporal stability.
- **Repetitions** — Proposed 27 saved fixtures x 2 settings. Temporal stability additionally needs a sequence with declared perturbations.
- **Acceptance** — Compare paired error distributions against a predeclared practical tolerance.
- **Limitations** — No estimator changes in this delivery. Static repeats do not measure temporal stability.

### 6 — Marker geometry

- **Hypothesis** — Wider and better distributed references affect interior geometric stability.
- **Independent variable** — Configured spacing, size and spatial distribution.
- **Controlled variables** — Camera, illumination, detector and arrangement.
- **Configuration and status** — Current v4 tested. New visual support layouts need explicit experimental configurations while preserving robot/board geometry.
- **Input** — RGB and measured/configured black-corner coordinates.
- **Permitted ground truth** — Independent board interior points and declared occlusion labels.
- **Metrics** — Residual, interior error, acceptance and occlusion sensitivity.
- **Repetitions** — Proposed 3 layouts x 9 views x 3 arrangements, 81 captures.
- **Acceptance** — A layout must meet independent interior-error and visibility budgets after mechanical qualification.
- **Limitations** — Current detector always requires four markers. Lower marker counts require a separately reviewed estimator/validity policy.

### 7 — Multiple cameras

- **Hypothesis** — Complementary views increase observation availability.
- **Independent variable** — One, two or three synchronized views and a declared selection rule.
- **Controlled variables** — Scene, detector, frame timing and per-camera calibration.
- **Configuration and status** — Pending. First compare availability with one H per camera, then predeclare selection/combination.
- **Input** — Timestamped camera RGB and per-camera explicit calibration.
- **Permitted ground truth** — Common scene for independent coverage evaluation.
- **Metrics** — Joint availability, selection correctness, per-camera error and total latency.
- **Repetitions** — Proposed 9 static scenes observed by 3 cameras, evaluate fixed subsets with scene-level denominators.
- **Acceptance** — Selection must use observable evidence, then be validated independently.
- **Limitations** — Viewpoint sweeps are sequential captures. 3D fusion requires synchronization, extrinsics and a geometric model.

### 8 — Physical grid or ChArUco

- **Hypothesis** — Known planar reference points can support calibration and independent validation.
- **Independent variable** — Reference type and separation of fitting/validation point sets.
- **Controlled variables** — Camera, plane and known dimensions.
- **Configuration and status** — Pending implementation and physical fixture authorization/measurements.
- **Input** — RGB, measured planar fixture geometry and explicit fit/holdout split.
- **Permitted ground truth** — Disjoint validation points or independently measured physical points.
- **Metrics** — Calibration error, holdout mapping error and coverage.
- **Repetitions** — Proposed 9 poses per fixture and a held-out point set. Physical trial counts depend on measurement repeatability.
- **Acceptance** — Accept only with independent error bounds and measured fixture uncertainty.
- **Limitations** — Green overlay supplies visualization only. Physical board alterations require approval.

### 9 — Environment and occlusion

- **Hypothesis** — A qualified system rejects inconsistent observations and recovers after visibility returns.
- **Independent variable** — Marker occlusion, arm pose, illumination, shadows and lens distortion.
- **Controlled variables** — One perturbation family at a time, recorded camera and base scene.
- **Configuration and status** — Missing-marker regression exists. Controlled capture sequences and calibrated distortion model are pending.
- **Input** — RGB with declared perturbation type, magnitude, seed and timestamps.
- **Permitted ground truth** — Independent validity/occlusion labels and projected points.
- **Metrics** — Correct rejection, incorrect acceptance, availability, geometry and recovery time.
- **Repetitions** — Proposed 9 baseline views x 3 declared perturbation levels per family. Recovery requires before/during/after sequence.
- **Acceptance** — Dangerous acceptance labels require declared geometry and mechanical budgets.
- **Limitations** — Native missing-reference warning combines visibility/inconsistency. Exact failure subtype and rejected-fit residual are not exported.

### 10 — Piece height and parallax

- **Hypothesis** — Raised surfaces bias board-plane foreground centroids.
- **Independent variable** — Existing mesh heights, piece type, square and offset, with declared camera views.
- **Controlled variables** — Accepted board geometry, illumination and estimator.
- **Configuration and status** — P035 diagnostic measured. A controlled geometry-aware study needs additional evaluator data, without changing piece meshes.
- **Input** — RGB and explicit optical/reference configuration.
- **Permitted ground truth** — Current body axes and actual mesh-surface geometry in evaluator only.
- **Metrics** — Projected centroid coverage, planar displacement by height/square, unknown rate.
- **Repetitions** — Proposed 6 piece types x 4 locations x 3 camera poses, 72 static fixtures, subject to available isolated views.
- **Acceptance** — Determine adequacy from actual grip-height clearance and independent observations.
- **Limitations** — Body XY is distinct from a measured grasp point. 2D centroids alone do not provide Cartesian 3D coordinates.



## Exact commands executed

Run from the repository root in Windows PowerShell. The first capture used an
exclusive output directory. Future executions must change output names.

~~~powershell
cmake --build build/p032-contract --config Release --target perception_image test_perception_offline test_piece_detector test_board_geometry test_camera_min_max

$exe = (Resolve-Path build/p032-contract/bin/Release/perception_image.exe).Path

& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/validate_native_perception.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --executable $exe --output simulation/mujoco/runs/p036/p033-repeat --azimuths 265 270 275

& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/validate_board_reference.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --assets docs/camera-rl/aruco-assets-v4 --executable $exe --output simulation/mujoco/runs/p036/p034-repeat --save-evaluator

& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/compare_perception_reproductions.py --p033 simulation/mujoco/runs/p036/p033-repeat --p034 simulation/mujoco/runs/p036/p034-repeat --audit simulation/mujoco/runs/p036/audit-before.json --output simulation/mujoco/runs/p036/reproduction-final

& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/qualify_saved_perception.py --source simulation/mujoco/runs/p036/p034-repeat --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --layout docs/camera-rl/aruco-assets-v4/layout.json --executable $exe --output simulation/mujoco/runs/p036/paired-final

& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/qualify_saved_perception.py --replay simulation/mujoco/runs/p036/paired-final/configuration.json --output simulation/mujoco/runs/p036/paired-replay

ctest --test-dir build/p032-contract -C Release --output-on-failure
$env:ACVISION_PERCEPTION_EXE = $exe
$env:P036_RUN_ROOT = (Resolve-Path simulation/mujoco/runs/p036).Path
& simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_native_perception.py simulation/mujoco/tests/test_perception_qualification.py -q -p no:cacheprovider
~~~

The archive contains an exploratory paired-v1 run as well as paired-final
and paired-replay. The published numbers use paired-final. All are preserved.
The configuration contains absolute artifact paths. Replay currently requires
those artifacts to remain available with matching contents at those paths.
Start manifests record Python/platform/package versions. Full dependency
identities include model files, native DLLs, executable, layout, capture source
and evaluator source. Raw artifact integrity is independently verifiable by hash.

To repeat safely in a new directory from saved data, use the following command.

~~~powershell
$next = Join-Path simulation/mujoco/runs/p036 ('replay-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/qualify_saved_perception.py --replay simulation/mujoco/runs/p036/paired-final/configuration.json --output $next
~~~

For metadata validation, evaluator files can be read before invoking a detector.
The native argument boundary still carries only image/output/layout. Geometric
evaluation uses the completed observation. The native module never receives a
MuJoCo handle, evaluator file, ground-truth coordinate or corrected detection.

## Evidence, validation and remaining work

- [Reproduction report](evidence-p036/reproduction-report.md) and
  [complete reproduction metrics](evidence-p036/reproduction-metrics.json).
- [Paired report](evidence-p036/paired-report.md) and
  [complete paired metrics](evidence-p036/paired-metrics.json).
- [Replay configuration](evidence-p036/paired-configuration.json) and
  [runtime manifest](evidence-p036/paired-manifest.json).
- [Initial audit](evidence-p036/audit-before.json) and
  [final validation](evidence-p036/validation.json).
- Full images, overlays, per-frame native JSON and independent projections remain
  in simulation/mujoco/runs/p036. Historical directories remain preserved.

The native suite passed 4/4 executables. Python regression passed 31 tests,
including 14 new infrastructure cases. Additional saved-run verification checks
artifact identity, replay equality and preservation after all documentation work.

First-delivery acceptance covers reproducible artifacts, correct denominators,
protected history, detector/evaluator separation and experiment-1 feasibility.
It does not establish a physical millimetre tolerance. The next experimental
increment should parameterize capture settings and run a matched camera/resolution
pilot before any detector refinement. Full ten-experiment implementation,
multicamera fusion, physical calibration and RL remain outside this delivery.
