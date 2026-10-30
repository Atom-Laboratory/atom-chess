# Main integration and experiment infrastructure — 2026-10-30

## Git integration

Fetched origin before merging. Starting simulation HEAD: 948f16a; main: f72c893.
Merge 8fbc7aa preserves both histories. Conflicts resolved in root/acvision CMake,
README and renamed Dockerfile. MuJoCo and operational ROS sources were preserved.
Preexisting untracked simulation/learning remains untouched and outside commits.
Windows case-collision deletions caused by merge checkout were rematerialized
from HEAD. No force push or shared-history rewrite was used.

Subsequent commits: 8000b3a fixes root motion/ament export behavior; 8bf8d67 adds
explicit experiment hooks/configuration/provenance; 04136ae fixes repository-wide
untracked detection and PowerShell UTF-8 BOM handling.

## Verified behavior

| Check | Result |
|---|---|
| C++ headless build, ROS environment sourced | Passed; 15 CTest suites |
| Existing ROS package build/Xacro/check_urdf | Passed |
| ROS tests | 13 pytest cases in four passing CTest suites; colcon reports 17 including wrappers |
| MuJoCo tests with ATOM_TEST_RENDER=1 | 25 passed |
| pip check | No broken requirements |
| Launcher demo | Finite, zero limit excess, final errors below 1.4e-15 in joint SI units |
| inspect_joints | Three isolated trials; replay_max_error=0 |

MuJoCo tests cover loading, initialization, state/commands, dynamics, limits,
reset/replay, bundle integrity, rendering, configurable tool pose, episode lifecycle,
invalid configuration/reward and record preservation. The contact test uses a
synthetic falling sphere/plane with positive normal force: robot contacts remain
unavailable. No throughput, learning or physical performance was measured.

Reproduce with the [manual](mujoco-user-guide.md). Root C++ tests ran in WSL with
GCC 15.2/OpenCV 4.10; Python tests ran in the Windows locked venv. Stockfish was
absent, so its UCI test was not registered. Firmware and hardware were not tested.

## Architecture and model audit after integration

The root CMake builds acvision, acchess, acmotion and integration from main.
They are available/tested libraries, not a complete autonomous game application.
Standalone ROS packaging of motion still needs dependency/export work.
The old nested description/control packages and Docker/Gazebo files are retained
as legacy sources, not the validated MuJoCo entry point.

MuJoCo uses direct Python reset/advance/observe/frame_pose. Episode delegates
task/observation/action/reward decisions to a researcher Task; no Gymnasium spaces
or agent are selected. ROS is optional future integration, outside per-step physics.
An eventual ROS bridge needs joint name/unit/frame mapping and one command owner.
No bridge or hardware transport was added.

The operational URDF remains an uncalibrated 2R+Z prototype. Known absent data:
verified joint frames/zeros/limits from authoritative F3D; J3 and gripper linkage;
servo-to-opening mapping; measured TCP; individual masses/COM/inertias; collision
geometry/friction; motor/transmission/force limits and latency. The Fusion gripper
evidence (-45 to +10 degrees about local Z) is insufficient to infer its parent,
zero and coupling. No dimensions or physical parameters were invented as facts.

Synthetic mass/inertia/gains and tool offsets are explicit and replaceable via
new bundles. Gravity/robot contacts remain disabled; pieces and gripper are fixed
visuals. Thus reaching-interface exercises are possible, physical grasping and
sim-to-real conclusions are not yet supported.

## Developer next steps

1. Follow the manual and inspect one joint at a time.
2. Choose an experimental tool point or extract a measured TCP from CAD.
3. Fill the task specification in the RL guide and implement Task personally.
4. Test reward/termination and a conventional baseline before selecting an algorithm.
5. Add Gymnasium only when spaces are defined; validate with its checker.
6. Close mechanical/contact/actuator evidence before manipulation or hardware work.

Decisions: [P003](../../../docs/adrs/P003-main-integration.md) and
[S005](../../docs/adrs/S005-experiment-boundaries.md).
