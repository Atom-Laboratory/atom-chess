# Native approach handoff qualification (M1)

The autonomous environment's opt-in `native_approach` reset uses the same
native Cartesian waypoint generator, IK, swept checks and MuJoCo executor as
the existing approach example. It skips randomized joint initialization and
keeps the robot at the executed approach endpoint. It compares measured and
planned joints, then checks a new native vision frame against the planned
homography and source position. Only a verified reset can build the actor's
first observation. That observation uses issued commands, RGB/vision and
configured task data. Measured joints and TCP are diagnostics.

## Measured results

Seeds 7 and 8 ran in each of the existing full-board and isolated-pawn scenes
with the lateral camera unchanged. All four planned and executed their direct
approach with the live sweep accepted. Arrival used wrist zero in both
fixtures. The table reports simulator model-relative tracking.

| Scene | Planned TCP height | TCP error, seeds 7 and 8 | Initialized |
| --- | ---: | ---: | ---: |
| Full board | 99.940 mm | 2.619 and 2.610 µm | 0/2 |
| Isolated e2 pawn | 75.940 mm | 2.619 and 2.610 µm | 0/2 |

All four resets reported `ARRIVAL_TARGET_NOT_VISUALLY_LOCALIZED`. The
rectified arrival image shows robot geometry in the target's image region.
The approach can meet tracking and collision requirements while obscuring
the target from the configured camera. In the repeat, the board reference
remained oriented even when target localization failed. The adapter keeps
local commands blocked and records that motion already occurred.

The machine-readable results are in the ignored local run directories
`simulation/mujoco/runs/native-handoff-m1-full-board-01` and
`native-handoff-m1-isolated-01` under the same parent. The `-02` repeats
also record homography shift and save the arrival RGB and rectified images.
Each output contains configuration and provenance, plus seed-level plans
and executed traces. Earlier experiments and checkpoints are preserved.

## Regression checks and next gate

The focused suite ran 33 passing tests and 3 skips with native fixture
variables unset. A separate run of the handoff test module with
`ATOM_HANDOFF_CONFIG` pointing at the isolated fixture passed all 11 tests.
It checked that identical RGB and issued commands produce identical actor
inputs even after hidden simulator positions and velocities change. The
success-path unit test uses synthetic arrival data to verify that the reset
uses the issued approach command and the new frame. It is interface coverage.

The next workspace qualification needs an endpoint that preserves target
visibility under the fixed camera, or a separately validated visual
tracking strategy through occlusion. This milestone does not qualify local
descent, grasp, lift, or any complete transfer. No PPO comparison was run.

See the [runner instructions](../../simulation/mujoco/training/autonomous-manipulation/README.md#m1-native-approach-handoff)
and [ADR S035](../../simulation/docs/adrs/S035-native-approach-episode-start.md).
