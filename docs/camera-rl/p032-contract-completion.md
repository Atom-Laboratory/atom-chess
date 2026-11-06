# P032 B1 acceptance completion — 2026-11-06

This increment completes the offline integration contract introduced in c005ccd.
It does not improve the existing detection algorithms. BoardDetector, Homography
and PieceDetector source files remain unchanged. Baseline branch: ros2_simulation.
Pre-existing monitor/playground changes, CAD and training data remain excluded.

## Architecture and changed files

`RGB PNG -> native OpenCV BGR decode -> validation -> BoardDetector -> Homography
-> PieceDetector -> schema 2 JSON / raw corners / rectified image / grid overlay`.

- `software/acvision/apps/perception_image.cpp`: CLI, explicit failure records,
  content identity, export and schema 2 serialization.
- `software/acvision/apps/perception_offline.hpp`: validation and orchestration
  shared with tests. No second detection algorithm.
- `software/acvision/tests/test_perception_offline.cpp`: native validation and
  direct-class equivalence tests.
- `software/acvision/CMakeLists.txt`: register test and build source identity.
- `simulation/mujoco/tests/test_native_perception.py`: negative fixtures,
  determinism, color boundary, output consistency and simulator isolation.
- `simulation/mujoco/examples/validate_native_perception.py`: richer experiment
  identity and schema check; truth still goes only to the evaluator.
- P032 ADR, this guide, README and evidence: decisions and measured results.

## Reproduce (PowerShell from repository root)

CMake >=3.23, C++17, OpenCV and GoogleTest are required. The existing Python MuJoCo
venv needs NumPy/Pillow/pytest, not Python OpenCV. The following is the tested local
build; change the generator/OpenCV path to match your machine. The GoogleTest
source override uses the existing local dependency and avoids network fetching.

```powershell
cmake -S software/acvision -B build/p032-contract -G 'Visual Studio 18 2026' -A x64 -DOpenCV_DIR=D:/opencv/build/x64/vc16/lib -DBUILD_TESTING=ON -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=F:/Users/EHD/Github/Atom/atom-chess/build/_deps/googletest-src
cmake --build build/p032-contract --config Release --target perception_image test_perception_offline test_piece_detector test_board_geometry test_camera_min_max
ctest --test-dir build/p032-contract -C Release --output-on-failure
$env:ACVISION_PERCEPTION_EXE = (Resolve-Path build/p032-contract/bin/Release/perception_image.exe).Path
& simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_native_perception.py -q -p no:cacheprovider
$run = Join-Path simulation/mujoco/runs ('p032-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/validate_native_perception.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --executable $env:ACVISION_PERCEPTION_EXE --output $run
```

Process an existing image without MuJoCo:

```powershell
& $env:ACVISION_PERCEPTION_EXE frame.png new-output --config acvision-defaults-800-v1
```

The optional configuration identifier selects only the built-in defaults profile:
800 pixel output, default PieceDetector brightness classifier, no optical/color
calibration. No arbitrary JSON configuration, externally supplied corners or
simulator pose is accepted. Unknown profile/options fail explicitly. This CLI does
not expose the library's optional HSV calibration loader in B1.

## Geometry and input contract

Homography::compute maps original decoded image pixel coordinates to rectified
pixel coordinates. Corners are TL/TR/BR/BL; destinations are (0,0), (800,0),
(800,800), (0,800). Homography::warp receives the original BGR image and that H,
not the internally blurred/grayscale detector image. Output is 800x800; the
continuous boundary at 800 differs from the last raster index 799. Default OpenCV
warp interpolation/border behavior is retained. This transform is not metric,
board-to-base, 3D pose or optical calibration.

Grid row/column indices are neutral image indices. Four corners do not identify
A1, board rotation, or any chess square. All square identities remain null.
Orientation requires a separate physical reference/calibration mechanism.

Decode with IMREAD_UNCHANGED. Accept only two-dimensional 8-bit three-channel BGR
matrices. RGB PNG encoding from Pillow becomes BGR through the OpenCV decoder;
no extra channel swap is performed. Grayscale, RGBA and higher-depth inputs are
rejected rather than silently coerced. EXIF auto-rotation is not applied in this
mode. Empty/malformed/missing images and unsupported dimensions/configuration
produce error records where a new output directory can be created.

Minimum width/height 27 follows the detector's cornerSubPix 11-pixel half-window
requirement (2*11+5). Corner validation rejects nonfinite, repeated, out-of-image,
nonconvex and less-than-one-source-pixel-area quadrilaterals. The one-pixel area
floor is a raster representability guard, not a physical calibration tolerance.
Finite nonsingular H is required; no scale-dependent determinant epsilon is used.
Rejected geometry is reported without inventing a rectification.

## Schema 2

The schema-1 evidence is retained unchanged. New consumers require schema_version=2.

| Field | Meaning |
|---|---|
| schema_version, implementation | Version 2, actual acvision_cpp |
| source_sha256, opencv_version | Build source identity, OpenCV runtime/build version |
| image_path, image_id, image_bytes | Absolute input path, FNV1a64 content fingerprint, byte count |
| image_width/height, decoded_channels, input_color | Decoded metadata; color null for unsupported input |
| configuration_id | Requested named profile (also on configuration error) |
| processing_completed, status | Diagnostic/export completed versus failed |
| board_detection_status | not_run, not_detected, rejected_geometry, unvalidated_candidate |
| orientation, calibration_status | unknown, absent |
| perception_valid, motion_ready | Always false in B1 |
| corners_px, homography | Actual available detector/transform results; otherwise null |
| homography_geometry | Direction, units, corner order, boundary, size, undistorted=false |
| cells | 64 actual classifier candidates if run; otherwise empty list |
| overlays | Relative artifact paths, or null if not generated |
| errors, warnings | Structured failure codes and explicit limitations |

Each cell contains candidate=empty/white/black from PieceDetector, while occupancy
remains unknown. Neither an empty candidate nor a successful process is confirmed
physical state. Confidence, piece center, chess square and gripper pose remain null.
No metric position, reliable visibility or orientation is invented.

CMake hashes the sorted relative filenames and SHA256 contents of core headers,
core sources and both bridge files; it automatically reconfigures when they change.
This identifies uncommitted source content as well as committed revisions. FNV is
only a convenient image identifier, not a security hash. The independent experiment
report additionally records SHA256 image/executable/model hashes, camera parameters
and MuJoCo version. Record toolchain versions with experiments for reproducibility.

Example successful diagnostic (excerpt, full example linked below):

```json
{
  "schema_version": 2,
  "processing_completed": true,
  "board_detection_status": "unvalidated_candidate",
  "orientation": "unknown",
  "calibration_status": "absent",
  "perception_valid": false,
  "motion_ready": false
}
```

Exit 0 means diagnostic processing/export completed even without a valid candidate.
Exit 2 means input/configuration/processing/output failure. A new directory is
reserved before input processing so rejected input can produce observation.json.
Invalid CLI argument count or output-reservation failure goes to stderr only.
Existing directories are never overwritten. I/O failure may leave partial artifacts;
inspect errors and processing_completed, not artifact existence alone.

Outputs: observation.json, corners.png when image processing succeeds, and
rectified.png plus rectified-grid.png only when H and classification are available.
The unannotated rectified image preserves intermediate pixels for comparison.
Raw overlays identify actual corner indices; grid overlays use only row,column.

## Executed validation

MSVC 19.50, OpenCV 4.12, MuJoCo 3.17.0, Windows. Native CTest: **4/4 executables
passed** (including three new native cases plus existing vision regression suites).
Python integration: **15 passed**. Native comparisons establish exact corner/H,
rectified pixel and 64-cell equivalence to independent direct class calls.

Negative tests include empty/undecodable/missing image, small dimensions,
unsupported channels/depth (depth also tested natively), invalid configuration,
blank image, large rectangle, sheet-like quadrilateral, table and cropped board.
Geometry tests cover repeated, collinear, subpixel-area, out-of-bounds, nonfinite
and concave corners. Rectangle/sheet tests deliberately record the current false
positive as an unvalidated candidate; they do not require an algorithm fix.

Color round-trip and repeated runs are deterministic. A separate isolation test
changes simulator qpos while keeping the input file identical and verifies identical
native JSON. The child executable receives only image/output/profile, not state.
Analytic projection and identity-grid tests exercise the independent evaluator.
No claim of exhaustive cross-platform/codec equivalence or physical accuracy is made.

## MuJoCo evidence and limits

New preserved run: `simulation/mujoco/runs/p032-contract-20261106`.
The three fixed lateral captures include all pieces, arm, gripper and graveyards.
No geometry or commanded motion was changed. This sweep retains the prior
experimental camera, not a measured mount. It does not cover all robot poses or
human-hand occlusion. View selected [artifacts and report](evidence-b1-contract/).

| Elevation | Center assignments | Nominal-equivalent mean error | Outcome |
|---|---:|---:|---|
| -35 | 0/64 | 1906.84 mm | Graveyard false positive |
| -45 | 62/64 | 8.48 mm | Candidate; p95 16.38 mm, max 19.91 mm |
| -55 | 0/64 | 1816.44 mm | Graveyard false positive |

Errors are rectified deviations scaled by experimental 35mm pitch, not physical
measurements. Evaluator chooses best D4 symmetry from ground truth; that optimistic
alignment does not supply orientation to perception. Huge errors flag a wrong
rectangle, not a realistic placement error. Metrics match the prior algorithm,
which was intentionally unchanged. Occupancy correctness is not certified.

## Acceptance and next step

B1 acceptance criteria 1–15 are satisfied for this supported Windows offline
integration: build, actual algorithms, valid/invalid inputs, geometry validation,
versioned JSON, overlays, documented geometry/limitations, simulator-image processing,
independent evaluation, boundary isolation tests, passing positive/negative tests,
recorded provenance and unchanged learning/hardware/physical-state flows.

This is completion of the bridge, not validated perception. Corner accuracy,
false rectangle rejection, orientation, optical/metric calibration and robust
occlusion handling remain pending for a separately scoped perception increment.
No PPO, P007 integration, hardware execution, bindings, RPC or algorithm correction
was introduced. Historical training checkpoints/results remain untouched.
