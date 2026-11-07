"""Export the six solid piece meshes from the ATOM slicer project in millimetres."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np


NAMES = dict(king='king', knight='knight', queen='queen', bishop='bishop',
             peon='pawn', rook='rook')
IDENTITY = np.array([1, 0, 0, 0, 1, 0, 0, 0, 1])


def export(source, output):
    with ZipFile(source) as archive:
        root = ET.fromstring(archive.read('3D/3dmodel.model'))
        if root.get('unit') != 'millimeter':
            raise ValueError('Expected a millimetre source')
        settings = ET.fromstring(archive.read('Metadata/model_settings.config'))
        objects = {obj.get('id'): obj for obj in root.findall('./{*}resources/{*}object')}
        meshes = {}
        for obj in settings.findall('object'):
            for part in obj.findall("part[@subtype='normal_part']"):
                name = Path(part.find("metadata[@key='name']").get('value')).stem.lower()
                kind = NAMES.get(name)
                if kind is None or kind in meshes:
                    continue
                component = objects[obj.get('id')].find(
                    f"./{{*}}components/{{*}}component[@objectid='{part.get('id')}']")
                transform = np.fromstring(component.get('transform'), sep=' ')
                if transform.shape != (12,) or not np.allclose(transform[:9], IDENTITY):
                    raise ValueError(f'Unexpected component rotation or scale for {kind}')
                path = next(value for key, value in component.attrib.items()
                            if key.endswith('}path')).lstrip('/')
                meshes[kind] = (path, part.get('id'), transform[9:])
        if set(meshes) != set(NAMES.values()):
            raise ValueError('Expected exactly the six recognized piece types')

        output.mkdir(parents=True, exist_ok=False)
        records = {}
        for kind, (path, object_id, translation) in sorted(meshes.items()):
            model = ET.fromstring(archive.read(path))
            if model.get('unit') != 'millimeter':
                raise ValueError(f'Unexpected component units for {kind}')
            mesh = model.find(f".//{{*}}object[@id='{object_id}']/{{*}}mesh")
            vertices = np.array([[float(v.get(axis)) for axis in 'xyz']
                                 for v in mesh.findall('./{*}vertices/{*}vertex')])
            faces = np.array([[int(t.get(axis)) for axis in ('v1', 'v2', 'v3')]
                              for t in mesh.findall('./{*}triangles/{*}triangle')])
            vertices += translation
            if not np.isfinite(vertices).all() or faces.min() < 0 or faces.max() >= len(vertices):
                raise ValueError(f'Invalid mesh coordinates or indices for {kind}')
            # The source pieces stand upright. Align the lowest face's bounds
            # with the XY origin and preserve vertex spacing and source yaw.
            bottom = vertices[:, 2].min()
            foot = vertices[np.isclose(vertices[:, 2], bottom, atol=1e-4, rtol=0)]
            center = (foot[:, :2].min(0) + foot[:, :2].max(0)) / 2
            vertices -= [*center, bottom]
            triangles = vertices[faces]
            normals = np.cross(triangles[:, 1] - triangles[:, 0],
                               triangles[:, 2] - triangles[:, 0])
            lengths = np.linalg.norm(normals, axis=1)
            normals /= np.where(lengths > 0, lengths, 1)[:, None]
            stl = np.zeros(len(faces), dtype=[('normal', '<f4', (3,)),
                                            ('points', '<f4', (3, 3)), ('attribute', '<u2')])
            stl['normal'], stl['points'] = normals, triangles
            asset = output / f'{kind}.stl'
            with asset.open('xb') as stream:
                stream.write(b'ATOM source piece mesh in mm'.ljust(80, b'\0'))
                stream.write(len(faces).to_bytes(4, 'little'))
                stl.tofile(stream)
            records[kind] = dict(source_part=path, source_object=object_id,
                                 size_mm=np.ptp(vertices, axis=0).round(4).tolist(),
                                 triangles=len(faces), degenerate_triangles=int((lengths == 0).sum()),
                                 sha256=hashlib.sha256(asset.read_bytes()).hexdigest())
            if len(faces) > 200_000:
                # MuJoCo rejects STL above 200k faces. Keep the indexed source
                # topology in OBJ as an alternate visual asset.
                obj_asset = output / f'{kind}.obj'
                with obj_asset.open('x', encoding='ascii') as stream:
                    np.savetxt(stream, vertices, fmt='v %.10g %.10g %.10g')
                    np.savetxt(stream, faces + 1, fmt='f %d %d %d')
                records[kind]['obj_sha256'] = hashlib.sha256(obj_asset.read_bytes()).hexdigest()
    (output / 'manifest.json').write_text(json.dumps(
        dict(source=source.name, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             units='millimetres', frame='foot centered in XY, lowest surface at Z=0, source yaw',
             use='visual reference meshes', pieces=records), indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    export(args.source, args.output)
