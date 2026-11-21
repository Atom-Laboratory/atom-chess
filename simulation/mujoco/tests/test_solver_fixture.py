import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.model import build_bundle


def test_solver_fixture_preserves_geometry_physics_inputs_and_source(tmp_path):
    module = Path(__file__).resolve().parents[1]
    source = tmp_path/'source'
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro', source, interactive=True, wrist=True)
    layout = tmp_path/'layout.json'
    layout.write_text('{"synthetic_test_only": true}')
    config = tmp_path/'environment.json'
    original_config = dict(bundle=str(source), layout=str(layout), camera={'test':1}, source='e2', target='e4')
    config.write_text(json.dumps(original_config))
    model_bytes = (source/'model.xml').read_bytes()
    manifest_bytes = (source/'manifest.json').read_bytes()
    path = module/'examples/qualify_hybrid_approach/prepare_solver.py'
    spec = importlib.util.spec_from_file_location('solver_fixture', path)
    prepare = importlib.util.module_from_spec(spec); spec.loader.exec_module(prepare)
    output = prepare.prepare_solver(config, tmp_path/'elliptic10')
    result = json.loads(output.read_text())
    before, after = Simulation(source), Simulation(result['bundle'])
    assert int(after.model.opt.cone) == 1 and after.model.opt.impratio == 10.
    assert int(after.model.opt.noslip_iterations) == 0
    for name in ('geom_size','geom_pos','geom_quat','geom_friction','geom_solref','geom_solimp',
                 'geom_contype','geom_conaffinity','body_mass','body_inertia','jnt_range',
                 'actuator_gainprm','actuator_forcerange','qpos0'):
        np.testing.assert_array_equal(getattr(before.model, name), getattr(after.model, name))
    assert after.model.opt.timestep == before.model.opt.timestep
    np.testing.assert_array_equal(after.model.opt.gravity, before.model.opt.gravity)
    assert {k:v for k,v in result.items() if k not in ('bundle','layout')} == {
        k:v for k,v in original_config.items() if k not in ('bundle','layout')}
    assert Path(result['layout']).read_bytes() == layout.read_bytes()
    assert (source/'model.xml').read_bytes() == model_bytes
    assert (source/'manifest.json').read_bytes() == manifest_bytes
    with pytest.raises(FileExistsError): prepare.prepare_solver(config, output.parent)
    with pytest.raises(ValueError): prepare.prepare_solver(config, tmp_path/'invalid', impratio=float('nan'))
