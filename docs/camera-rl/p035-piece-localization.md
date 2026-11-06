# P035 — Current-piece localization experiment

The native acvision adapter can now compare a current frame with an empty-board
frame. Capture both with the same camera, resolution, exposure, lighting and arm
pose. Place the arm out of the board's line of sight for the capture. The adapter
registers each frame separately with the same four ArUco markers.

From the repository root, run these commands in PowerShell.

```powershell
cmake --build build/p032-contract --config Release --target perception_image
$exe = (Resolve-Path build/p032-contract/bin/Release/perception_image.exe).Path
& $exe current.png new-diagnostic-directory --reference docs/camera-rl/aruco-assets-v4/layout.json --empty-board empty.png
```

Look for cyan crosses in `rectified-grid.png`. Each cross is the centroid of a
foreground component within one canonical square. Components crossing a square
boundary, clipped at the board edge or competing within a square yield unknown
coordinates. The background threshold (35 per BGR channel), opening (5 px
ellipse) and minimum area (200 px²) are experimental settings for 800 px
rectification. The optional JSON fields are
`foreground_centroid_rectified_px`, `foreground_status` and
`empty_board_image_id`. The centroid lies in the board-plane image projection.
It has no height, verified occupancy or usable grip pose. `piece_center` remains
null and `motion_ready` remains false. Missing or inconsistent markers in
either image suppress all centroid output.

To reproduce the simulator experiment, choose an unused output directory.

```powershell
$run = Join-Path simulation/mujoco/runs ('p035-' + [guid]::NewGuid().ToString('N'))
& simulation/mujoco/.venv/Scripts/python.exe -B simulation/mujoco/examples/validate_board_reference.py --bundle simulation/mujoco/runs/playground-fingertip-only-v1 --assets docs/camera-rl/aruco-assets-v4 --executable $exe --output $run --evaluate-foreground
```

Repeat with `--elevations -65 -75 -85` and a fresh output. To reproduce the
high-camera marker adjustment, also pass
`--layout docs/camera-rl/evidence-p035/high-camera-layout.json`. That experimental
layout moves marker 3 from u=-220 mm to u=-380 mm for clearance. It is a
simulation fixture. Use measured geometry for physical installation.

Each sweep includes nine camera angles for each of four arrangements. The
relocated arrangement moves the pawns originally at e2 and d7 to f4 and b5
with small XY offsets. The detector receives only the two images and marker
layout. The evaluator compares the output with MuJoCo piece-body XY in each
occupied square. Report denominators include rejected frames.

| Camera / layout | Accepted frames | Initial matched | Offset matched | Relocated matched |
|---|---:|---:|---:|---:|
| -35/-45/-55°, P034 layout | 32/36 | 5/288 | 0/288 | 0/18 |
| -65/-75/-85°, P034 layout | 0/36 | 0/288 | 0/288 | 0/18 |
| -65/-75/-85°, marker 3 moved | 36/36 | 75/288 | 65/288 | 7/18 |

At the higher angles with marker 3 moved, matched initial positions had mean
error 0.75 mm and maximum 6.45 mm. Offset positions had mean 1.17 mm and maximum
13.27 mm. Relocated pawns had mean 3.41 mm and maximum 5.54 mm. Those metrics
cover the returned candidates only. Empty cases produced zero candidates and
there were zero candidates assigned to empty squares in these fixtures.

The higher view improves coverage and reduces parallax, but the arm remains
visible over the playing surface in the tested pose. The strict component
rule also rejects adjacent silhouettes that merge. Use these findings to
choose camera placement and an arm observation pose, then measure the camera
intrinsics, board-to-base registration and actual gripper clearance. Qualify
a geometry-aware grasp estimator and visual verification before using these
observations in a MOVE or RL environment.

See the raw reports and experimental layout in [evidence-p035](evidence-p035/).
