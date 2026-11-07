# P013 — Official piece mesh provenance

## Context

The current manipulation fixture uses procedural primitives for contact and
appearance. The supplied ChessPieces.3mf is a Bambu Studio project in
millimetres. Its metadata identifies Danner34 and declares CC0. The accompanying
Blender file is an authoring asset. The 3MF provides the measured mesh input
for this extraction.

## Decision

Export six visual references by reading named normal parts and their component
references. Exclude support blockers and print-plate placement. Preserve scale
and source yaw. Center the lowest face in XY and place it at Z=0. Export binary
STL per piece and an indexed OBJ when the face count exceeds the MuJoCo STL
reader limit. Record asset hashes and full mesh extents. Keep the CAD inputs and
generated meshes outside the source commit.

## Evidence and limits

| Piece | Maximum X × Y × Z (mm) | Faces |
|---|---:|---:|
| Pawn | 18.05 × 18.05 × 34.63 | 35,422 |
| Rook | 23.21 × 23.21 × 43.09 | 24,182 |
| Knight | 32.75 × 25.92 × 54.44 | 902,216 |
| Bishop | 25.86 × 25.86 × 56.84 | 43,603 |
| Queen | 25.90 × 25.90 × 62.72 | 36,406 |
| King | 25.92 × 25.92 × 71.23 | 28,746 |

Five STLs and the knight OBJ compiled as individual visual geoms using MuJoCo
3.17.0 with a 0.001 scale on all axes. The knight STL exceeded the loader limit.
The source pawn contains two zero-area triangles. Compilation does not establish
watertightness, resting stability, grasps or clearance. No mass, inertia or friction
was inferred. The STL files use millimetres by convention, with units recorded
in the manifest.

## Alternatives and consequences

A whole print plate would bake in duplicate placements and helper volumes.
Using these detailed visuals as contact hulls would hide concavities and could
alter grasp behavior. The simulation migration will require separate collision
geometry, compatible grasp points and validation with adjacent pieces.

## Reproduce

From the repository root in PowerShell:

```powershell
& ./simulation/mujoco/.venv/Scripts/python.exe simulation/mujoco/examples/export_atom_piece_meshes/run.py hardware/Project/chess_pieces/ChessPieces.3mf simulation/mujoco/runs/official-piece-exports
```

The output path must be new. Use the manifest to verify the source and asset hashes.
