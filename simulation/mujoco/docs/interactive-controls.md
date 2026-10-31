# Interactive controls, gravity and contacts

## Start on Windows

1. Close old MuJoCo viewers. Each window has independent simulation state.
2. Open PowerShell in the repository and run:

```powershell
cd F:\Users\EHD\Github\Atom\atom-chess
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode view
```

3. Use the **ATOM controls** panel next to the 3D viewer. Each joint has a
   bidirectional slider and minus/plus buttons. The status shows actual position,
   simulation time and contact count. Sliders set targets, not measured positions.
4. Open gripper / Close gripper moves both fingers. Independent finger sliders
   are available for debugging. Close is -0.01 m; open is +0.02 m per finger.
5. Pause freezes physics. Hold sets the measured positions as targets. Reset
   restores a raised home pose (Z=0.12 m); Camera restores the initial viewpoint.
6. Close either window to stop. An initialization exception is printed in the
   terminal; keep it available when reporting a problem.

Keyboard shortcuts work when the **3D viewer** has focus:

| Keys | Control |
|---|---|
| Q / A | First revolute joint forward / backward |
| W / S | Vertical Z up / down |
| E / D | Last arm revolute joint forward / backward |
| O / C | Open / close gripper |
| P | Toggle physics pause |
| Space | Hold current measured joint positions |
| R | Reset robot and time |
| V | Restore camera |

Keyboard and +/- buttons use 1% of the corresponding joint range per event;
targets clamp at joint limits. Mouse drag/scroll in the viewer rotates/zooms
the camera. The built-in actuator panels are hidden to avoid conflicting controls.
Do not interpret Hold as a physical emergency stop.

## What changed in v4

The launcher now selects **runs/interactive-chess-v4**, automatically building it
with `--interactive`. Existing v1-v3 results remain untouched. Gravity is
[0,0,-9.81] m/s². The robot is fixed to its base; dynamic links and fingers respond
to gravity. Position servos hold the synthetic load with finite tracking error.
The demo shows about 5.1 mm of Z error under gravity, not the previous near-zero
zero-gravity error. This is not measured robot accuracy.

Collision hulls are separate from visual meshes. Robot hulls collide with the
floor, board frame and anchored piece primitives. Board tiles remain visual to
avoid contact seams. Collision geoms are invisible and in group 3. Lighting,
near/far clipping and multisampling are set explicitly. Viewer physics changes
use its lock; sync is called outside that lock.

**Limits:** gripper motion is an experimental parallel-slide approximation,
not the Fusion linkage. Finger mass=0.03 kg, inertia=0.00005 kg m² per diagonal,
gain=150, damping gain=5, force range ±8 N, nominal speed=0.025 m/s. These are
synthetic settings. Arm gain=500 and damping gain=30. No measured servo mapping,
TCP or force calibration is claimed. Convex hulls can overestimate solid regions.
Self-collision is intentionally filtered; pieces stay anchored. Contact reporting
is available, but grasping and dynamic pick/place are not implemented.

The new model has five controlled coordinates: [first revolute rad, Z m, last
arm revolute rad, finger 1 m, finger 2 m]. Use the manifest to determine names.
Existing three-coordinate exercises must use a v3 bundle. Never send a v4 vector
to hardware/acmotion: finger slides are not physical servo coordinates.

## Developer steps

1. Read interactive_model.py: it transforms the diagnostic scene after URDF
   conversion and records assumptions in the manifest.
2. Change source/profile, not generated XML. Build a fresh bundle:

```powershell
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
$bundle = 'simulation/mujoco/runs/interactive-' + [guid]::NewGuid().ToString('N')
& $atomPy -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --output $bundle --interactive
& $atomPy -m atom_mujoco.cli view --bundle $bundle
```

3. Test bidirectional commands, reversal, limits and finger opening/closing.
4. Lower Z and verify contact names in observe()['contacts']; inspect hull
   placement before changing the collision filters or claiming fidelity.
5. Run regression tests, including a renderer on a machine with OpenGL:

```powershell
$env:ATOM_TEST_RENDER = '1'
& $atomPy -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode demo
```

Verified: **28 tests passed**. New cases check bidirectional jogging/clamps,
finger close/open/reopen, actual gravity descent with actuators disabled, and
robot/environment contact without nonfinite states or warnings. Native panel
and viewer initialized and closed cleanly in a timed smoke run. Offscreen v4
render was inspected. This does not certify every camera angle or manual input.

Tkinter is part of the tested Windows Python distribution. If missing, install
a Python distribution with Tcl/Tk support; headless demo/tests do not require it.
Do not use the old viewer to assess the new scene. If the launcher already has
a v4 bundle from before a source edit, use the fresh-bundle commands above.

Reference: [official passive viewer API](https://mujoco.readthedocs.io/en/stable/python.html),
[MJCF physics and visualization](https://mujoco.readthedocs.io/en/stable/XMLreference.html).
