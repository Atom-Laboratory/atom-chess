from pathlib import Path
import mujoco
import numpy as np
import pytest
from atom_mujoco.model import build_bundle
from atom_mujoco.playground import Playground


@pytest.fixture
def playground(tmp_path):
    source=Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    build_bundle(source,tmp_path/'bundle',interactive=True)
    return Playground(tmp_path/'bundle')


def test_required_e2_e3_is_not_falsely_reported_success(playground):
    result=playground.execute(operation='MOVE',piece_id='white_pawn_e2',source='E2',target='E3')
    assert result['status']=='FAILED'
    assert 'Unreachable' in result['error_code']
    assert not result['grasp_confirmed'] and not result['visual_confirmed']
    assert not result['history']
    revision = playground.physical.confirmed.revision
    second = playground.execute(operation='MOVE', source='e2', target='e3')
    assert second['reconciliation_required']
    assert playground.physical.confirmed.revision == revision
    assert not second['history']


def test_ik_reachable_target_does_not_mutate_physics(playground):
    sim=playground.sim
    sim.reset([.2,.12,.3,0,0])
    point=sim.frame_pose('grasp_center')['position_m']
    before=sim.data.qpos.copy()
    q=playground.solve(point)
    np.testing.assert_array_equal(before,sim.data.qpos)
    sim.reset(q)
    np.testing.assert_allclose(sim.frame_pose('grasp_center')['position_m'],point,atol=.001)


def test_rl_cannot_be_selected_without_checkpoint(playground):
    result=playground.execute(operation='MOVE',piece_id='white_pawn_e2',source='e2',target='e3',controller='rl')
    assert result['status']=='FAILED' and 'RL_POLICY_UNAVAILABLE' in result['error_code']


def test_experimental_board_e2_e3_physically_moves_pawn(tmp_path):
    import json
    module = Path(__file__).resolve().parents[1]
    parameters = json.loads((module/'examples/playground-board.json').read_text())
    bundle = tmp_path/'playground'
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro', bundle,
                 interactive=True, parameters=parameters)
    playground = Playground(bundle, diagnostic_unchecked=True)
    result = playground.execute_request(dict(schema=1, operation='MOVE', source='e2', target='e3'))
    assert result['status'] == 'COMPLETED_SIMULATION_ORACLE', result['error_code']
    assert result['grasp_confirmed'] and result['release_confirmed']
    pawn = playground.sim.data.body('white_pawn_e2').xpos
    target = playground.sim.frame_pose('square_center_e3')['position_m']
    np.testing.assert_allclose(pawn[:2], target[:2], atol=.002)
    assert playground.physical.confirmed.occupancy['e3'] == 'white_pawn_e2'
    assert playground.physical.confirmed.occupancy['e2'] is None
    assert playground.physical.confirmed.revision == 1
    before = playground.sim.data.time
    result = playground.execute_request(dict(schema=1, operation='MOVE', source='e3', target='e2'))
    assert result['status'] == 'COMPLETED_SIMULATION_ORACLE', result['error_code']
    assert playground.sim.data.time > before
    assert playground.physical.confirmed.revision == 2
    assert playground.physical.confirmed.occupancy['e2'] == 'white_pawn_e2'


def test_request_rejects_extra_identity_and_unknown_schema(playground):
    for request in (dict(schema=1, operation='MOVE', source='e2', target='e3', piece_id='x'),
                    dict(schema=2, operation='MOVE', source='e2', target='e3')):
        with pytest.raises(ValueError, match='envelope'):
            playground.execute_request(request)
    assert playground.physical.confirmed.revision == 0


def test_feedback_detects_external_piece_displacement(playground):
    sim = playground.sim
    body = sim.model.body('white_pawn_e2').id
    qadr = sim.model.jnt_qposadr[sim.model.body_jntadr[body]]
    sim.data.qpos[qadr] += .02
    mujoco.mj_forward(sim.model, sim.data)
    result = playground.execute(operation='MOVE', source='e2', target='e3')
    assert result['status'] == 'FAILED'
    assert 'AMBIGUOUS_LOCATION' in result['error_code']
    assert result['reconciliation_required']
    assert playground.physical.confirmed.occupancy['e2'] == 'white_pawn_e2'
