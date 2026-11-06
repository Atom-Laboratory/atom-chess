# Native acvision bridge — Phase B1

The offline executable now runs the real C++ BoardDetector, Homography and
PieceDetector on MuJoCo RGB captures (PNG acquisition decoded as BGR by OpenCV).
No duplicate Python vision algorithm or simulated corners are passed to acvision.
This is diagnostic processing, not an approved observation source for motion/RL.

## Build and run (Windows PowerShell, repository root)

Use fresh paths; adjust OpenCV and generator to the installed toolchain:

```powershell
cmake -S Software/acvision -B build/acvision-perception -G 'Visual Studio 18 2026' -A x64 -DOpenCV_DIR=D:/opencv/build/x64/vc16/lib -DBUILD_TESTING=OFF
cmake --build build/acvision-perception --config Release --target perception_image
$env:ACVISION_PERCEPTION_EXE = (Resolve-Path build/acvision-perception/bin/Release/perception_image.exe).Path
& simulation/mujoco/.venv/Scripts/python.exe -B -m pytest simulation/mujoco/tests/test_native_perception.py -q -p no:cacheprovider
$run = Join-Path simulation/mujoco/runs ('perception-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/validate_native_perception.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --executable $env:ACVISION_PERCEPTION_EXE --output $run
```

The Python environment requires the existing MuJoCo package, NumPy, Pillow and
pytest for tests. It does not require Python OpenCV. DLLs are copied by CMake.
No visualizer window opens: inspect lateral PNGs, corners.png, rectified-grid.png
and report.json in the new output directory. Previous outputs cannot be overwritten.
The native executable also accepts any image directly:

```powershell
& $env:ACVISION_PERCEPTION_EXE path/to/frame.png path/to/new-output-directory
```

Exit 0 means diagnostic processing succeeded, not that a board was reliably found.
Invalid input or existing output returns 2. Read status and motion_ready in JSON.
No-candidate output contains null homography and no cells. Candidate output contains
64 row/column records, unvalidated color/occupancy, null confidence, unknown
visibility, null square identity and no gripper pose. Orientation is not inferred.
The input is not undistorted; use ideal simulated pinhole images for this experiment.
Hardware frames require a subsequent calibrated preprocessing contract.

## Validation evidence (2026-11-05)

Built with MSVC 19.50, OpenCV 4.12, CMake Visual Studio 18 2026. The existing
BoardDetector float conversion warning remains; build completed.
Native integration tests: **3 passed in 0.71 seconds**. Coverage includes missing
image, blank frame, output preservation, synthetic board processing, native H
mapping of four corners, 64-cell contract, null reliability fields, overlay size,
analytic evaluator projection and identity mapping of all 64 centers.
These tests verify transport/schema/geometry mechanics, not detector accuracy.
No direct-library-versus-executable exhaustive parity benchmark has been completed.

The fixed ideal-pinhole camera is evaluated at provisional distance .85 m,
azimuth 270 degrees (black side of this scene) and elevations -35/-45/-55 degrees.
These are a candidate sweep, not measurements of a physical mount. Every capture
uses the same intact initial model with all pieces, robot and graveyards.
No camera noise, hand occlusion model or dynamics randomization is included yet.

| Elevation | Correct center assignments | Mean nominal-equivalent error | Result |
|---|---:|---:|---|
| -35 degrees | 0/64 | 1906.8 mm | Graveyard rectangle mistaken for board |
| -45 degrees | 62/64 | 8.48 mm | Biased board corners; p95 16.38 mm, max 19.91 mm |
| -55 degrees | 0/64 | 1816.4 mm | Graveyard rectangle mistaken for board |

These errors are rectified-grid deviations converted using the experimental 35 mm
pitch, NOT physical calibration measurements. Huge errors describe an invalid
homography candidate, not a plausible robot placement error. The evaluator chooses
the best of eight grid symmetries with ground truth solely for diagnostics; this
optimistic alignment is NOT vision orientation. No measured a1 orientation exists.

See [recorded report](evidence-b1/report.json), [candidate overlay](evidence-b1/corners-45.png)
and [false detection](evidence-b1/corners-55.png). The corresponding rectified grid
is [here](evidence-b1/rectified-grid-45.png). Visual inspection confirms false
rectangle selection and silhouette overlap. Occupancy accuracy has not yet been
quantified; its presence in the output is not evidence of valid physical occupancy.

## Architecture boundary and remaining blocker

The executable accepts only an image pathname and output directory. Simulator
projections live in evaluator-only JSON; they are never supplied to the detector.
No policy is present and no physical state is committed. Camera gripper pose,
confidence, calibration and square orientation remain unavailable.

The current detector is not reliable enough to advance to a camera-based RL
training environment. Following the requested stop-on-blocker rule, this increment
ends at B1 integration and initial B2 measurement, not at training. The next
coherent increment must validate the checker pattern (reject graveyard/other
rectangles), fix projective outer-corner estimation, establish orientation,
represent unknown/occluded cells and repeat occupied-board calibration tests.
A measured board-to-base transform and conventional verified manipulation baseline
are still prerequisites. Existing PPO and checkpoints are unchanged.

## Superseding contract

The initial schema and missing equivalence coverage above are historical. See [P032 contract completion](p032-contract-completion.md) for schema 2, the expanded tests and current instructions.
