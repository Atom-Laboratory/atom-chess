"""Inspect binary STL geometry without assuming its assembly axes are global axes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def inspect(meshes):
    meshes = Path(meshes)
    records = []
    for part in ('gripper_hand1', 'gripper_hand2'):
        raw = (meshes/(part+'.stl')).read_bytes()
        triangles = np.frombuffer(raw, offset=84, dtype=np.dtype([
            ('normal', '<f4', 3), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')]))['vertices'].astype(float)
        cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        area = np.linalg.norm(cross, axis=1)/2
        normals = cross/np.maximum(2*area[:, None], 1e-15)
        groups = {}
        for normal, weight in zip(normals, area):
            if normal[np.argmax(abs(normal))] < 0:
                normal = -normal
            key = tuple(np.round(normal, 4))
            groups[key] = groups.get(key, 0)+float(weight)
        tangent = np.array(max(groups, key=groups.get))
        tangent /= np.linalg.norm(tangent)
        rail = np.cross(tangent, [0, 1, 0])
        rail /= np.linalg.norm(rail)
        vertices = triangles.reshape(-1, 3)
        tips = vertices[vertices[:, 1] < -10]  # Export frame, mm.
        records.append(dict(part=part, sha256=hashlib.sha256(raw).hexdigest(),
                            dominant_face_normal=tangent.tolist(), rail_axis=rail.tolist(),
                            tip_rail_bounds_mm=[float(min(tips@rail)), float(max(tips@rail))],
                            tip_tangent_bounds_mm=[float(min(tips@tangent)), float(max(tips@tangent))]))
    return dict(units='mm', source='exported STL; not servo/linkage calibration', parts=records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meshes', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.meshes), indent=2))
