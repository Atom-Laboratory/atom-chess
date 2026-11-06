from types import SimpleNamespace

import mujoco
import numpy as np

from atom_mujoco.collision import SweptChecker, SceneCollision


def checker(obstacle_y):
    model = mujoco.MjModel.from_xml_string(f'''<mujoco>
      <worldbody><geom name="obstacle" type="sphere" size=".01" pos="0 {obstacle_y} 0"/>
      <body><joint name="slide" type="slide" axis="1 0 0" range="-1 1"/>
      <geom name="moving" type="sphere" size=".01" mass="1"/></body></worldbody></mujoco>''')
    return SweptChecker(model, np.zeros(1), [0], [(0,1)])


def test_swept_detects_between_clear_endpoints():
    value = checker(0)
    assert value.interval([-.1], [.1])['status'] == 'collision'


def test_swept_certifies_clear_path_with_subdivision():
    value = checker(.04)
    assert value.interval([-.1], [.1]) is None
    assert value.samples > 1


def test_unresolved_intervals_fail_closed():
    value = checker(.04)
    value.max_depth = 0
    assert value.interval([-.1], [.1])['status'] == 'unresolved'


def test_preflight_does_not_mutate_live_scene(tmp_path):
    from pathlib import Path
    from atom_mujoco.model import build_bundle
    from atom_mujoco.playground import Playground
    module = Path(__file__).resolve().parents[1]
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro',tmp_path/'bundle',interactive=True,
                 parameters={'board_center_m':[.28,.10,.012]})
    playground = Playground(tmp_path/'bundle')
    # Make an explicit blocked fixture: ordinary descents may now be feasible.
    playground.sim.model.geom_size[playground.sim.model.geom('white_pawn_d2_base').id,0] = .04
    mujoco.mj_forward(playground.sim.model, playground.sim.data)
    before = playground.sim.data.qpos.copy()
    result = playground.execute(operation='MOVE', source='e2', target='e3')
    assert result['collision_checked']
    assert not result['collision_report']['valid']
    assert 'COLLISION_PREFLIGHT_FAILED' in result['error_code']
    np.testing.assert_array_equal(playground.sim.data.qpos,before)
    assert playground.physical.confirmed.revision == 0
    assert not result['reconciliation_required']
    retry = playground.execute(operation='MOVE', source='e2', target='e3')
    assert 'COLLISION_PREFLIGHT_FAILED' in retry['error_code']
    np.testing.assert_array_equal(playground.sim.data.qpos,before)


def test_crowded_e2_e4_uses_preshape_and_verified_feedback(tmp_path):
    import json
    from pathlib import Path
    from atom_mujoco.model import build_bundle
    from atom_mujoco.playground import Playground
    module = Path(__file__).resolve().parents[1]
    parameters = json.loads((module/'examples/playground-reachable-board.json').read_text())
    # Visual meshes are irrelevant to these unchanged physical proxies.
    parameters['official_piece_visuals'] = False
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro', tmp_path/'bundle',
                 interactive=True, parameters=parameters)
    playground = Playground(tmp_path/'bundle')
    try:
        initial = playground.sim.data.qpos.copy()
        result = playground.execute(operation='MOVE', source='e2', target='e4')
        assert result['status'] == 'COMPLETED_SIMULATION_ORACLE', result['error_code']
        assert result['collision_report']['valid']
        assert result['grasp_confirmed'] and result['release_confirmed']
        assert not result.get('runtime_collision')
        assert playground.physical.confirmed.occupancy['e2'] is None
        assert playground.physical.confirmed.occupancy['e4'] == 'white_pawn_e2'
        assert playground.physical.confirmed.revision == 1
        phases = {p['phase']:np.array(p['end']) for p in result['collision_report']['trajectory']}
        assert phases['preshape'][3] < phases['approach'][3]
        assert phases['open'][3] == phases['preshape'][3]
        assert phases['fully_open'][3] == playground.sim.upper[3]
        # Reproduce the previous wide-open descent on independent preflight data.
        playground.sim.data.qpos[:] = initial
        mujoco.mj_forward(playground.sim.model, playground.sim.data)
        solutions = [phases[p] for p in ('approach','descend','lift','transport','place')]
        destination = playground.sim.data.body('white_pawn_e2').xpos.copy()
        destination[:2] = playground.feedback.endpoint_position('e4')[:2]
        rejected = SceneCollision(playground.sim).check_plan(
            solutions, 'white_pawn_e2', destination, aperture=0.,
            grasp=result['grasp_opening_m'])
        assert not rejected['valid'] and rejected['phase'] == 'descend'
        assert 'white_pawn_d2_base' in rejected['failure']['geoms']
        np.testing.assert_array_equal(playground.sim.data.qpos,initial)
    finally:
        playground.ledger.close()
