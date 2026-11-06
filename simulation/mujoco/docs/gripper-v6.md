# v6 gripper alignment: user and developer steps

The previous fingers moved along assembly Z instead of their inclined guides.
v6 uses the direction extracted from the exported finger faces, with matching
pad orientation and opposing coupled travel. This remains a simplified parallel
mechanism; the physical Fusion servo linkage is not yet reconstructed.

## Run

1. Close previous MuJoCo/control windows.
2. From the repository root in Windows PowerShell run:

```powershell
& ./simulation/mujoco/scripts/Start-MuJoCo.ps1 -Mode view
```

3. Confirm the new bundle directory is assets/bundles/interactive-chess-v6.
4. Use Open/Close buttons or O/C with viewer focus. Open now means 0 m relative
   to the exported mesh pose; close means -0.021 m on each opposed slide.
5. Observe fingers following the inclined rails without rotating or shifting
   their common midpoint. Move slowly around pieces and reset when needed.

Do not reuse v5 target values: positive finger displacement is outside v6 limits.
The panel reads limits from the bundle automatically. Pieces remain dynamic.

## Reproduce the geometry analysis

```powershell
$atomPy = '.\simulation\mujoco\.venv\Scripts\python.exe'
& $atomPy simulation/mujoco/examples/inspect_gripper_geometry/run.py --meshes simulation/src/meshes
$env:ATOM_TEST_RENDER = '1'
& $atomPy -m pytest simulation/mujoco/tests -q
Remove-Item Env:ATOM_TEST_RENDER
```

The inspection reports hashes, dominant face normals and fingertip bounds.
Expected rail direction is approximately [-0.60609,0,0.79539], in the original
assembly frame. Do not interpret it as world Z or a calibrated servo axis.
See interactive_model.py for explicit pad positions, orientations and stroke.
Tests cover geometry alignment at multiple arm poses, coupled finger travel,
gravity, contacts, and isolated physical pawn lift/release without attachment.
The isolated fixture validates contact mechanics, not reliable pickup from every
occupied board square. Full linkage extraction and real dimensions remain pending.

Decision and evidence: [ADR S009](../../docs/adrs/S009-mesh-aligned-gripper.md).
