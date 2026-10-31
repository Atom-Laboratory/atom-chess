# v5: coupled gripper and movable chess pieces

## Run the current scene

1. Close old viewer/control windows.
2. Open Windows PowerShell in the checkout:

```powershell
cd F:\Users\EHD\Github\Atom\atom-chess
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode view
```

3. Confirm the launcher uses **runs/interactive-chess-v5**. Existing v4 files
   are intentionally not modified. A running old viewer cannot load new code.
4. Use the shared finger slider or Open/Close buttons (O/C in the 3D window).
   Both fingers now have equal targets. The second independent slider is removed.
5. Align the dark fingertip pads on opposing sides of a piece's narrow stem.
   Lower slowly with Z, close, wait for contact, then raise Z slowly. Gripping a
   rounded top at its edge can eject a piece; closing near neighbors can push them.
6. Open to release. Pieces now move, tip and fall under gravity. Reset restores
   their original positions as well as the robot. Pause stops all physics.

This is manual joint control, not automatic square alignment or pick planning.
No guarantee is made that every initial-board piece is reachable or graspable
with the current uncalibrated arm geometry and dense starting arrangement.
Contact counts now include pieces resting on the board; a nonzero count does
not by itself prove a grasp. Observe contacts with finger_1_pad/finger_2_pad and
verify that the piece actually rises and remains held.

## Developer model and interface changes

- Each of the 32 pieces is a free rigid body. Synthetic mass/inertia and friction
  are recorded in ADR S008; they are not measurements of physical chess pieces.
- Fingers use opposed slides constrained to equal displacement, plus one shared
  target. Unequal commands raise ValueError before physics advances.
- Localized pad colliders replace entire-finger convex hulls. Other robot hulls
  are still approximate; self-collision and the actual Fusion linkage remain pending.
- Five controls remain [first revolute rad, Z m, last arm revolute rad, finger 1 m,
  finger 2 m], with equal finger targets. Full mjData.qpos also contains 32 free
  body poses. Use Simulation.observe()['position'] for controlled coordinates;
  never assume nq equals actuator count.
- Finger equality permits small contact-dependent deviations. It is not a rigid
  reconstruction of the real servo/link mechanism or a physical calibration.
- No grasp weld or hidden attachment is created. Lifting requires frictional contact.

## Reproduce the isolated grasp regression

```powershell
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $atomPy -m pytest simulation/mujoco/tests/test_interactive.py -k dynamic_pawn -v
$env:ATOM_TEST_RENDER = '1'
& $atomPy -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
```

Verified: **30 tests passed**. The isolated test moves other pieces away during
fixture setup and places a pawn at [0.373,-0.0905,0.0182] m with arm targets
[0,0.0115,0,0,0]. After setup, it only commands physics: settle, close to -0.01 m,
raise Z by 0.08 m, open to 0.02 m, then check gravity-driven release. The pawn
rises more than 0.06 m and returns within 0.002 m of its initial support height.
Reset must restore the pawn's original square and zero all velocities.
This is a reproducible contact fixture, not an autonomous board pickup demo.

For a modified source, generate a fresh bundle rather than editing a compiled XML:

```powershell
$bundle = 'simulation/mujoco/runs/grasp-' + [guid]::NewGuid().ToString('N')
& $atomPy -m atom_mujoco.cli build --urdf simulation/src/urdf/atom.urdf.xacro --output $bundle --interactive
& $atomPy -m atom_mujoco.cli view --bundle $bundle
```

Inspect model.py, interactive_model.py, backend.py and test_interactive.py before
changing joint order or contact filters. Preserve three-axis diagnostic bundles
for older learning exercises. No hardware or RL training is part of this update.
