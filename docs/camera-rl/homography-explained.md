# Homography implementation walkthrough

## Coordinate system and mathematics

The camera sees the board as a perspective quadrilateral. acvision estimates a
3 x 3 matrix H from original image pixels (x,y) to canonical board pixels (u,v).
Compute q = H [x,y,1]^T, then u = q0/q2 and v = q1/q2.

H has eight independent parameters because its overall scale cancels during
division. Four non-collinear correspondences can determine H. The current
ArUco route fits sixteen correspondences together.

The canonical image is 800 x 800 px, with a8 at top-left, h8 at top-right,
h1 at bottom-right and a1 at bottom-left. Each cell is 100 x 100 px.
Inside the board, column = floor(u/100), row = floor(v/100), file = 'a'+column
and rank = 8-row. The center of e2 is (450,650).
The continuous outer boundary uses coordinates 0 and 800. Raster indices run
from 0 through 799.

## What changed

| Increment | Change | Consequence |
|---|---|---|
| P033 | Remove rectangle-only fallback and require 7 x 7 checker intersections. Fit the grid projectively using all 49 intersections, then project its outer 0..8 corners. | Corrects perspective extrapolation and rejects unrelated rectangles. Occupied-board detection still passed only 2/9 views. |
| P034 | Fit four identified ArUco markers to explicit board coordinates using their 16 corners. | Board orientation and square coordinates become independent of piece arrangement. |
| P034 | Enable CORNER_REFINE_SUBPIX. | Refines detected marker corners to fractional image pixels before fitting. |
| P034 | Correct mirrored marker texture UVs and move references out of robot occlusion. | Makes the rendered IDs readable and visible in the tested views. |
| P034 | Increase rendering from 1280 x 960 to 1920 x 1440. | Accepted coverage rose from 18/27 to 24/27 in the documented experiments with the same residual budget. |
| P035 | Register current and empty-board images separately before comparing foreground. | Reuses the same homography estimator and adds current-piece evidence after rectification. |

The adapter selects the checker route without --reference and the ArUco route
with --reference. The latter requires all four configured markers per frame.

## Current native pipeline

1. Read DICT_4X4_50 marker IDs and their configured canonical corner coordinates.
   IDs 0,1,2,3 establish orientation through the installation layout.
2. Detect markers using native OpenCV ArucoDetector and refine their corners
   with CORNER_REFINE_SUBPIX.
3. Match each configured ID once and concatenate all 16 image/board point pairs.
   Unconfigured IDs contribute no points.
4. Fit H with cv::findHomography(src,dst,0). The implementation uses method 0.
5. Project the detected corners through H. Reject a nonfinite/singular matrix
   or maximum corner residual above the configured limit of 5 canonical px.
6. Use the inverse H to locate the board boundary in the original image.
   Validate finite, convex corners inside the input image.
7. Reuse Homography::warp and cv::warpPerspective to resample the frame into
   an 800 x 800 image. Divide it into 64 cells.
8. In P035 diagnostic mode, compare separately rectified current and empty
   frames and draw cyan crosses at accepted foreground centroids.

The corner residual measures agreement at points used for fitting.
Independent board-point evaluation is therefore required to assess mapping
quality. Each frame gets a fresh estimate. Missing or inconsistent required
references cause geometry to become unknown.

## Layout and physical installation

For a square board of side L millimetres, set the origin at outer a8,
u toward h8 and v toward a1. A marker corner at (u_mm,v_mm) maps to
(800*u_mm/L,800*v_mm/L). Marker corners outside the board can have negative
coordinates or coordinates above 800. Use black-pattern corners in printed
TL/TR/BR/BL order.

The experimental P034 scene has a 280 mm playable side and 35 mm squares.
The 5 px residual budget corresponds nominally to 1.75 mm on that plane.
Physical gripping tolerances require measured tool and piece clearances.

The marker black pattern is 40 mm wide, with 4 mm white margins per side.
Measure the black-pattern corners and keep reference surfaces coplanar with
the playing surface. The installation guide specifies centers and orientation.
P035's high-camera alternative moves marker 3 from u=-220 mm to u=-380 mm,
with both the layout and rendered geometry changed together.

Real-camera use requires measured reference placement, camera intrinsics and
distortion handling, followed by calibration into the robot base coordinates.
acmotion's CoordinateMapper handles calibrated robot-base square positions.

## Independence from piece placement

Current piece identity, color and starting square do not enter H fitting.
ArUco IDs and their installed positions define the board coordinate system.
P034 compared initial, empty and displaced-piece arrangements. At each tested
camera pose they produced the same mapping and acceptance decision.

Pieces and the robot can still occlude markers. Maintaining reference visibility
and a useful observation pose is part of camera installation and execution.

## Measured results and interpretation

P034 accepted 24/27 frames. Every accepted frame assigned 64/64 board centers
correctly, with mean nominal planar error about 0.43–0.65 mm.
The independent evaluator projected known board-surface centers and compared
them directly to named canonical square centers. Reference-mode evaluation
uses the configured orientation without oracle rotation/reflection alignment.
Simulator state is used by the evaluator. The detector receives image and layout.

Perspective rectification corrects points on the board plane. Raised pieces
retain parallax. Their apparent centers and silhouettes can be displaced in
the rectified image, especially in lateral views.

P035 measures piece localization separately. After the high-camera layout
adjustment it matched 147/594 expected occupied-square observations across
the tested arrangements and views. Robot occlusion and merged silhouettes
limit coverage. A visually regular grid and incomplete piece localization
can occur in the same frame. Qualifying a grasp estimator requires independent
error measurements at the intended gripping height.

## Code and reproduction

- [Reference detector](../../software/acvision/include/board_reference/board_reference.hpp)
  loads the layout, detects/refines markers and fits/rejects H.
- [Offline orchestration](../../software/acvision/apps/perception_offline.hpp)
  selects the route, checks board corners and rectifies the image.
- [Homography implementation](../../software/acvision/src/homography/homography.cpp)
  provides the perspective warp.
- [Checker detector](../../software/acvision/src/board_vision/board_vision.cpp)
  contains the P033 grid extrapolation.
- [Installation guide](aruco-installation-guide.md) provides printing,
  placement, build commands and the 27-scene reproduction.
- [P035 guide](p035-piece-localization.md) provides foreground and camera tests.
- [P034 report](evidence-p034/report.json) and [P035 reports](evidence-p035/)
  preserve measurements and source/layout/model identities.
- [ADR P034](../adrs/P034-explicit-board-visual-reference.md) and
  [ADR P035](../adrs/P035-image-evidence-for-piece-location.md) record decisions.