# P034 — ArUco installation and developer guide

Status (2026-11-06): native reference integration tested in simulation. Physical
installation/calibration and actual piece grasp localization are NOT validated.
This guide is in English for developers. The user approved printed references.

## What markers do, and what they do not do

Four fixed DICT_4X4_50 markers establish the board plane and orientation from RGB.
The native acvision detector estimates image -> canonical 800x800 homography using
all sixteen marker corners. IDs uniquely identify references. Every accepted image
requires all four configured IDs, no duplicates and acceptable reprojection error.
Missing/inconsistent references invalidate the frame: no cached H and no checker
fallback. Pixel refinement uses OpenCV CORNER_REFINE_SUBPIX.

The canonical image has a8 at top-left, h8 top-right, h1 bottom-right, a1 bottom-left.
This orientation comes from the supplied installation layout, NOT piece colors,
initial pawn positions, or a simulator pose. PieceDetector still produces only
unvalidated occupancy/color candidates; unknown occupancy is not silently committed.

`MOVE(source_square,target_square)` remains the task interface. Markers define
where a square is, independent of what piece occupies it or where that piece began
the game. Current physical state and current vision must resolve the object and
its offset within the source square. Changing the board arrangement must not change
square coordinates. A displaced piece needs a changed grasp point, not a changed
square address. Visual piece-center localization, height/grasp verification and
board-to-robot metric calibration are separate pending capabilities. P034 does not
claim to implement or execute them. It issues no hardware or motion commands.

## Printable files and experimental layout

Use only [aruco-assets-v4](aruco-assets-v4/) for the currently tested layout.
Earlier generated assets are development attempts, NOT installation recommendations.
The generator now produces v4. SVG files encode physical dimensions; PNGs are
texture/raster assets and may print at an incorrect size if automatically fitted.

- Print each SVG at **100% / actual size**, never fit-to-page.
- Measure the outer black pattern: **40 x 40 mm** in this experimental template.
- The white quiet margin is **4 mm each side**, total paper square **48 x 48 mm**.
- Use matte high-contrast paper, rigid flat backing and no cropping of white margins.
- Keep IDs and orientations exactly as generated. Labels go outside the white margin.
- Keep marker surfaces coplanar with the playing square surface. Putting them on
  the table below a raised board invalidates the common-plane assumption.
- Attach supports to the board so they cannot slide independently. Check camera
  coverage and arm occlusion before permanent mounting.

The tested simulation has a **280 x 280 mm playable area** (35 mm squares). That is
an experimental scene dimension, not a measurement of your modular printed board.
For this scene define (u,v) in mm: origin at outer a8 corner, u toward h8, v toward a1.
The following are **black-square center** coordinates (not paper edges):

| ID | Side reference | u (mm) | v (mm) | Reason |
|---|---|---:|---:|---|
| 0 | beyond a8 | -120 | -80 | Clear of board and graveyard |
| 1 | beyond h8 | 400 | -80 | Clear of board and graveyard |
| 2 | beyond h1 | 400 | 280 | Clear of gripper in tested home pose |
| 3 | beyond a1 | -220 | 280 | Extra offset avoids the robot column |

Viewed with a8 at the top-left, the TOP edge of every printed marker points toward
rank 8; their printed images are not rotated or mirrored relative to each other.
Their configuration lists black-square corners in printed TL/TR/BR/BL order.
The far-left marker is intentionally asymmetric to clear the current robot column.
The entire support footprint is much wider than the board. These supports are
experimental visual surfaces, not fabricated collision-qualified CAD parts.

**Do not blindly copy these offsets to a differently sized physical board.**
Assemble your interlocking board first. Measure its playable width/height and
reference corner coordinates in the same (u,v) frame, then update the layout.
The current renderer requires a square board matching board_side_mm. For a
rectangular measured surface, normalize u and v by their measured width/height
separately; validate that the resulting grid represents the actual 8x8 squares.
Marker locations may change to avoid physical occlusion, but their measured corner
coordinates and rotations must change in the JSON too.

## Calibration file

`aruco-assets-v4/layout.json` is the simulation template. It records schema=1,
dictionary, orientation, rectified_size=800, marker print dimensions, provenance,
max_reprojection_error_rectified_px and four marker corner arrays.

For measured black corners (u,v), enter `(800*u/board_width_mm,
800*v/board_height_mm)` into corners_rectified_px. Negative values and values above
800 are expected for markers outside the playable board. Do not use paper corners.
Do not infer these coordinates from piece placement. Re-measure after changing
supports or assembling a different board. Archive a new configuration; its content
fingerprint appears as reference_id in output.

The example residual threshold is **5 rectified pixels** (1.75 mm at the simulated
35 mm pitch), a provisional geometry diagnostic budget, not a safe grasp tolerance.
Do not increase it merely to accept a poor frame. Real optics require independently
measured intrinsics/distortion and an appropriate undistortion boundary; the current
CLI reports physical_unvalidated and undistorted=false. P034 does not install a
fake camera calibration or derive the robot-base transform from homography alone.

## Build and use

From repository root, with the existing P032 OpenCV build configured:

```powershell
cmake --build build/p032-contract --config Release --target perception_image generate_board_reference test_perception_offline
ctest --test-dir build/p032-contract -C Release --output-on-failure
$exe = (Resolve-Path build/p032-contract/bin/Release/perception_image.exe).Path
& $exe frame.png new-diagnostic-directory --reference docs/camera-rl/aruco-assets-v4/layout.json
```

New assets can be produced with `generate_board_reference.exe NEW_DIRECTORY`.
It refuses existing directories. Do not regenerate over existing measurements.

To repeat the 27-scene experiment:

```powershell
$run = Join-Path simulation/mujoco/runs ('p034-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/validate_board_reference.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --assets docs/camera-rl/aruco-assets-v4 --executable $exe --output $run
```

Simulation reference planes are added only to a new diagnostic XML. Original
bundle/checkpoints remain untouched. References are visual-only, coplanar surfaces;
they are not collision-enabled mounts and are not CAD-accurate mechanical fixtures.
The native executable receives only RGB image file and explicit layout config.
Projection ground truth exists only in the independent evaluator. There is no D4
oracle orientation alignment in this experiment: configured a8 orientation is
compared directly to the named square centers.

## Results and remaining limitations

The initial texture was mirrored; fixing UV orientation exposed actual marker IDs.
Early symmetric layouts put marker 3 behind the robot column. The tested v4 layout
clears that column for the home pose. Refining marker corners reduced raster error;
raising image resolution from 1280x960 to 1920x1440 improved accepted coverage from
18/27 to **24/27** while retaining the same residual threshold.

Final experiment: azimuth 265/270/275 degrees, elevation -35/-45/-55, distance 1.05 m,
fixed lookat at scene board center; initial pieces, no pieces, and per-piece offsets
(+/-4 mm X, +/-3 mm Y). Every accepted frame assigns **64/64 squares** correctly.
Mean nominal-equivalent error is approximately **0.43–0.65 mm** in accepted frames.
The three failures are the same 265/-55 camera view in all arrangements; all IDs
are visible but the fit exceeds the configured residual limit. No fallback occurs.
These are ideal-pinhole simulation diagnostics, not real-world accuracy claims.

Native tests: four CTest executables passed. Python integration: **17 passed**,
including explicit a8/h1 addressing, missing-marker invalidation and duplicate-ID
configuration rejection. Native reference test checks subpixel control-point
mapping within half a raster pixel and loss of visibility. No moving-arm coverage,
hand occlusion, lens distortion, physical mounting errors or measured grasp trials
have passed yet.

Across the three piece arrangements, detection decisions and square errors match
at every tested camera pose. That validates independence of the BOARD REFERENCE
from those piece arrangements. It does not prove arbitrary piece localization or
successful MOVE execution. The next implementation work remains current-piece
localization and visual execution verification; marker fit alone cannot authorize
motion, and perception_valid/motion_ready remain false.
