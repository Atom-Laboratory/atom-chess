# ATOM MuJoCo operational guide

Run this module in **Windows PowerShell**. ROS/WSL is for separate C++/ROS work.
Verified: Python 3.12.14, MuJoCo 3.17.0, NumPy 2.5.4 and pytest 9.2.0.
OpenGL is needed for visualization; a paid GPU or service is not required.
Linux/ARM installation remains unverified. Do not share Windows venvs with WSL.

## 1. Install and verify

For a fresh checkout with Python 3.12 and its launcher installed:

```powershell
cd F:\Users\EHD\Github\Atom\atom-chess
py -3.12 -m venv simulation/mujoco/.venv
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $atomPy -m pip install -r simulation/mujoco/requirements-windows-py312.lock
& $atomPy -m pip install -e 'simulation/mujoco[test]'
& $atomPy -m pip check
& $atomPy -m pytest simulation/mujoco/tests -q
```

Reuse an existing venv. Expected: no broken requirements; 24 tests pass and one
render test skips. With ATOM_TEST_RENDER=1: 25 pass. No C++ build is required here.

## 2. Open and control

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode view
```

The launcher creates runs/upright-chess-v3 if missing. Focus the viewer:
Q/A changes the first revolute target; W/S the vertical prismatic target;
E/D the final revolute target. R resets; Space holds the current position as a
target, not an instantaneous brake. Close the viewer to exit.
The scene has an upright arm, rigid gripper, board and 32 fixed visual pieces.
Gripper opening and piece manipulation are unavailable.

To build a fresh portable model without the launcher:

```powershell
$bundle = 'simulation/mujoco/runs/manual-' + [guid]::NewGuid().ToString('N')
& $atomPy -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --output $bundle
& $atomPy -m atom_mujoco.cli view --bundle $bundle
```

Each bundle contains XML, seven STL assets, configuration and hashes. Build
requires a new directory. The launcher reuses existing bundles: after source
changes build a fresh one and specify its --bundle explicitly.

## 3. Run scenarios and record results

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode demo
$result = 'simulation/mujoco/runs/exercise-' + [guid]::NewGuid().ToString('N') + '.json'
& $atomPy simulation/mujoco/examples/inspect_joints.py --bundle simulation/mujoco/runs/upright-chess-v3 --output $result
$image = 'simulation/mujoco/runs/view-' + [guid]::NewGuid().ToString('N') + '.ppm'
& $atomPy -m atom_mujoco.cli render --bundle $bundle --output $image
```

Demo runs four simulated seconds without a window: expect finite=true, small
errors and zero limit excess in this scenario. Inspection moves each joint and
replays the sequence; verified replay_max_error=0. This is conventional control,
not learning or measured physical accuracy. JSON contains versions, commit,
dirty/untracked flags, manifest and wall time. Preserve bundle/lock with results.
runs is Git-ignored; back it up separately. A SHA cannot reproduce dirty task code.

## 4. Read state and send commands

Start `& $atomPy`, then enter:

```python
from atom_mujoco.backend import Simulation
sim = Simulation('simulation/mujoco/runs/upright-chess-v3')
print(sim.names)
state = sim.reset(seed=7, randomize=True)
for _ in range(200):
    state = sim.advance([0.3, 0.08, -0.4])

print(state['position'], state['velocity'], state['joint_limit_excess'])
print(sim.frame_pose('arm2_frame'))
print(sim.frame_pose('square_center_e4'))
sim.reset()
exit()
```

Order: joint_base_to_link1 (rad), joint_z_axis_arm1 (m),
joint_arm1_link_arm2_link (rad). Default interval: 0.02 s. position is integrated
state; target is requested position; reference is the speed-limited servo reference.
Returned arrays are copies. frame_pose returns world metres and a 3x3 rotation.
arm2_frame is the last joint origin, not a calibrated gripper tip. Rotating that
joint changes orientation without translating its own origin.

## 5. Change experimental parameters

build --parameters accepts JSON keys: mass_kg_per_moving_body,
diagonal_inertia_kg_m2, joint_damping, joint_armature, actuator_kp, actuator_kv,
timestep_s, control_substeps and tool_offset_in_arm2_m. Positive finite values
are required; inertia must satisfy triangle inequalities; substeps is an integer.
Tool offset requires three finite metres. Dynamic overrides apply to all joints.
These are hypotheses, not identified motor parameters.

The following is a **synthetic teaching offset**, not a CAD measurement:

```powershell
$config = 'simulation/mujoco/runs/parameters-' + [guid]::NewGuid().ToString('N') + '.json'
'{"actuator_kp":40.0,"tool_offset_in_arm2_m":[0.12,0,0]}' | Set-Content -Encoding utf8 $config
$toolBundle = 'simulation/mujoco/runs/tool-' + [guid]::NewGuid().ToString('N')
& $atomPy -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --parameters $config --output $toolBundle
& $atomPy -m atom_mujoco.cli view --bundle $toolBundle
```

Read frame_pose('experimental_tool') or observe()['tool_pose'] in that bundle.
Without an offset tool_pose is None; tcp_calibrated remains false. Gravity and
robot contacts stay disabled. Enabling them requires reviewed physical data and
collision geometry. Never bypass integrity checks by editing a compiled XML.

## 6. Develop and diagnose

| Location | Responsibility |
|---|---|
| simulation/src/urdf and meshes | Operational prototype sources |
| simulation/mujoco/src/atom_mujoco/model.py | Converter, profile and bundles |
| chess_scene.py | Visual pieces and square references |
| backend.py | reset/advance/observe/frame_pose |
| experiment.py | Task protocol and Episode lifecycle |
| recording.py | Records and provenance |
| examples/inspect_joints.py | Public API example |
| tests | FK, dynamics, reset, limits, records and rendering |

Add scenarios with explicit resets/targets/configuration and replay checks.
After changing geometry/physics, create a new bundle, inspect its manifest and run:

```powershell
$env:ATOM_TEST_RENDER = '1'
& $atomPy -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
```

For the separate C++ core, enter WSL, navigate to the checkout and run:

```bash
cmake -S . -B build/headless -DACCHESS_BUILD_VIEWER=OFF
cmake --build build/headless -j 4
ctest --test-dir build/headless --output-on-failure
```

ROS may be sourced during this root build. Standalone motion ROS packaging is
unverified. simulation/src is the operational ROS package; nested packages
inherited from main are legacy, outside the validated launch path.

- Existing output: choose a fresh GUID path.
- ImportError: check the venv and editable installation.
- No movement in another viewer: demo/viewer are independent processes.
- OpenGL failure: run headless checks and investigate context/driver errors.
- Old model: rebuild into a fresh directory.
- Hash mismatch: restore/regenerate the bundle; retain integrity checks.
- NaN/warnings: stop, inspect parameters and reset.
- contacts=None means unavailable. Constraints are soft: monitor excess.

The contact fixture tests a synthetic sphere/plane, not robot collisions.
URDF inertial tags are not imported. See the [integration report](integration-report.md)
and [RL guide](../../docs/learning/rl-getting-started.md).
