"""Copy a verified fixture for an explicit contact-solver comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from atom_mujoco.backend import Simulation


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_solver(config_path, output, *, cone='elliptic', impratio=10.):
    config_path, output = Path(config_path).resolve(strict=True), Path(output).resolve()
    if cone not in ('pyramidal', 'elliptic') or not np.isfinite(impratio) or impratio <= 0:
        raise ValueError('Known friction cone and positive finite impedance ratio required')
    if output.exists():
        raise FileExistsError('Use a fresh solver fixture directory')
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    source = Path(config['bundle']).resolve(strict=True)
    if output.is_relative_to(source):
        raise ValueError('Derived fixture must be outside its source bundle')
    original = Simulation(source)  # Verify source model and all asset hashes first.
    before = dict(cone=int(original.model.opt.cone), impratio=float(original.model.opt.impratio),
                  noslip_iterations=int(original.model.opt.noslip_iterations))
    if before['noslip_iterations'] != 0:
        raise ValueError('Controlled comparison requires NoSlip disabled in the source')
    bundle = output/'bundle'
    bundle.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    for filename in [*manifest['assets_sha256'], 'model.xml']:
        path = (source/filename).resolve(strict=True)
        if not path.is_relative_to(source):
            raise ValueError('Bundle asset escapes source directory')
        destination = bundle/filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    tree = ET.parse(bundle/'model.xml')
    option = tree.getroot().find('option')
    if option is None:
        raise ValueError('Explicit source physics option required')
    option.set('cone', cone)
    option.set('impratio', str(float(impratio)))
    tree.write(bundle/'model.xml', encoding='utf-8', xml_declaration=True)
    manifest['model_sha256'] = sha(bundle/'model.xml')
    manifest['profile']['contact_solver_comparison'] = dict(cone=cone, impratio=float(impratio),
                                                           scope='experimental; not hardware calibrated')
    (bundle/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    derived = Simulation(bundle)
    layout = Path(config['layout']).resolve(strict=True)
    layout_copy = output/'reference-layout.json'
    shutil.copyfile(layout, layout_copy)
    config.update(bundle=str(bundle), layout=str(layout_copy))
    (output/'environment.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    provenance = dict(schema=1, source_config=str(config_path), source_config_sha256=sha(config_path),
        source_model_sha256=sha(source/'model.xml'), derived_model_sha256=sha(bundle/'model.xml'),
        layout_sha256=sha(layout), solver_before=before,
        solver_after=dict(cone=int(derived.model.opt.cone), impratio=float(derived.model.opt.impratio),
                          noslip_iterations=int(derived.model.opt.noslip_iterations)),
        declared_changes=['option.cone', 'option.impratio'], mujoco_version=mujoco.__version__,
        preparation_source_sha256=sha(Path(__file__)), training_eligible=False)
    (output/'solver-provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    return output/'environment.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cone', choices=('pyramidal', 'elliptic'), default='elliptic')
    parser.add_argument('--impratio', type=float, default=10.)
    args = parser.parse_args()
    print(prepare_solver(args.config, args.output, cone=args.cone, impratio=args.impratio), flush=True)


if __name__ == '__main__':
    main()
