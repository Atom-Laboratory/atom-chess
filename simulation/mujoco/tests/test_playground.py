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
