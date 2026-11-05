# Core module integration status

## Synchronization

The local ros2_simulation branch started at 24ca912 and already contained
origin/ros2_simulation at 4f8e0ff. Fetch found no new commits on that branch.
origin/main remained at 8d9894c. The separate observation-consistency branch
advanced to 2a23796 with explicit promotion confirmation. It is not part of
the tracked simulation branch. Local CAD, simulation/jsons and
simulation/learning remain outside the commits.

## Current boundaries

| Module | Implemented | Remaining |
|---|---|---|
| acvision | Board corners, homography, cell segmentation and occupancy by color. The detector takes OpenCV images. The integration adapter checks observation consistency. | A fixed MuJoCo camera in the shared observation path, camera distortion calibration, orientation evidence, explicit uncertainty, piece type and confidence. The current BoardObservation is separate from the canonical logical Board. |
| acchess | Canonical Board, FEN, movement and king-safety checks, capture and special-move flags, and a Linux UCI session with bounded I/O. EngineTurnPlan validates the engine proposal and delegates physical decomposition. | Application orchestration for pending turns and physical confirmation, and explicit game outcome handling including repetition and draw adjudication. |
| acmotion | Calibrated coordinate mapping, ordered TaskPlanner transfers, Cartesian waypoints, joint IK, motion transport interface and segment execution. The Python Playground enforces P007 and runs a nominal swept check. | The Playground must consume C++ MotionPlanner output. Geometry mapping to simulated and real axes, clearance of the actual controller path and the physical serial backend remain open. |

## Official piece geometry

The 3MF and Blender source are under hardware/Project/chess_pieces. The
exported visual meshes and manifest are in its exports directory locally.
See [P013](../adrs/P013-official-piece-mesh-provenance.md) for dimensions, scale
and mesh issues. The Playground still uses procedural contact geometry.
Official contact shapes, stable support and gripper clearance require separate
verification. Mass, inertia and friction remain experimental.

## Verify the engine boundary

On Linux or WSL with CMake, OpenCV and a real Stockfish executable:

```bash
cmake -S . -B build/headless -DACCHESS_BUILD_VIEWER=OFF -DSTOCKFISH_EXECUTABLE=/usr/games/stockfish
cmake --build build/headless -j 4
ctest --test-dir build/headless --output-on-failure
ctest --test-dir build/headless -R test_board_move_adapter -V
```

The real engine test sends FEN for two successive positions over one UCI
session, validates both proposals, and checks that the physical request
matches the validated move and the original board stays unchanged until the
test advances it explicitly. The fixture uses a synthetic coordinate mapper.
The same test suite works without Stockfish by omitting the engine-specific
case. The existing protocol tests cover timeout and error handling separately.

The end-to-end scenario remains open. The remaining boundary is to feed the
engine-selected physical plan to the MuJoCo controller, verify geometry and
trajectory, then confirm the transfer from fresh evidence. Current collision
failures must remain visible during qualification.
