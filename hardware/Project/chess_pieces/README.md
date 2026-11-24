# Chess-piece source assets

ChessPieces.3mf and chessPieces.blend are the supplied source files.
exports/manifest.json records the source identity, millimetre dimensions and
hashes of per-kind reference meshes.

The MuJoCo bundle builder reads the exported STL files for five kinds and
knight.obj for the knight. The repository explicitly allows that Wavefront OBJ
through the generic compiler-object ignore rule. The original knight STL is
also preserved as a hardware/source export.

To verify the exported inputs, run from the repository root.

~~~powershell
& simulation/mujoco/.venv/Scripts/python.exe -B -c "import hashlib,json,pathlib; p=pathlib.Path('hardware/Project/chess_pieces/exports'); m=json.loads((p/'manifest.json').read_text()); assert all(hashlib.sha256((p/(k+('.obj' if k=='knight' else '.stl'))).read_bytes()).hexdigest()==v['obj_sha256' if k=='knight' else 'sha256'] for k,v in m['pieces'].items()); print('piece exports verified')"
~~~

Build and exercise the current model using the
[MuJoCo README](../../../simulation/mujoco/README.md).
Piece visualization meshes and physical collision proxies have separate roles.
The current simulation dynamics remain experimental.
