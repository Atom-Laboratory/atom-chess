from dataclasses import replace
from pathlib import Path
import json

import mujoco
import numpy as np
import pytest

from atom_mujoco.model import build_bundle
from atom_mujoco.playground import Playground
from atom_mujoco.task_plan import validate_plan
from atom_mujoco.physical_state import Location, PhysicalBoardState


def plan(*transfers):
    return dict(schema=2, operation='PLAN', transfers=[dict(source=a, target=b) for a,b in transfers])


@pytest.fixture
def scene(tmp_path):
    module = Path(__file__).resolve().parents[1]
    params = json.loads((module/'examples/playground-board.json').read_text())
    params['graveyard_slots'] = {'slot_0': [.24, -.10, .012]}
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro', tmp_path/'scene', parameters=params, interactive=True)
    return Playground(tmp_path/'scene', diagnostic_unchecked=True)


def test_graveyard_in_physics_and_observation(scene):
    sim = scene.sim
    geom = sim.model.geom('graveyard_support_slot_0').id
    assert sim.model.geom_contype[geom] != 0
    assert 'slot_0' in scene.physical.confirmed.graveyard_slots
    body = sim.model.body('black_pawn_d7').id
    address = sim.model.jnt_qposadr[sim.model.body_jntadr[body]]
    sim.data.qpos[address:address+3] = [.24, -.10, .019]
    mujoco.mj_forward(sim.model, sim.data)
    for _ in range(100):
        sim.advance(sim.target)
    observed = scene.feedback.snapshot(0)
    assert observed.by_id['black_pawn_d7'].location == Location('graveyard', 'slot_0')


def test_whole_plan_reserves_and_rejects_conflicts_before_execution(scene):
    before = scene.sim.data.qpos.copy()
    request = plan(('e7', 'graveyard:slot_0'), ('e2', 'e7'))
    assert len(validate_plan(request, scene.physical.confirmed)) == 2
    for bad in (plan(('e2','e7'), ('e7','graveyard:slot_0')),
                plan(('e7','graveyard:slot_0'), ('d7','graveyard:slot_0')),
                plan(('e7','graveyard:unknown'))):
        with pytest.raises(ValueError):
            scene.execute_request(bad)
    np.testing.assert_array_equal(scene.sim.data.qpos, before)


def test_partial_plan_preserves_confirmed_removal(scene, monkeypatch):
    # State orchestration fault injection; not evidence of a physical capture.
    def execute(**kwargs):
        if kwargs['target'].startswith('graveyard:'):
            snapshot = scene.physical.confirmed
            identity = snapshot.occupancy[kwargs['source']]
            pieces = tuple(replace(p, location=Location('graveyard', 'slot_0'))
                           if p.identity == identity else p for p in snapshot.pieces)
            scene.physical = PhysicalBoardState(replace(snapshot, pieces=pieces, revision=1),
                                               position_tolerance_m=.003, angle_tolerance_rad=.15)
            return dict(status='COMPLETED_SIMULATION_ORACLE', error_code=None)
        return dict(status='FAILED', error_code='injected second-step failure')
    monkeypatch.setattr(scene, 'execute', execute)
    result = scene.execute_request(plan(('e7','graveyard:slot_0'), ('e2','e7')))
    assert result['status'] == 'FAILED'
    assert result['completed_transfers'] == 1
    assert scene.physical.confirmed.occupancy['e7'] is None
    assert scene.physical.confirmed.occupancy['e2'] == 'white_pawn_e2'


def test_physical_capture_removes_before_attacker(scene):
    # Explicit physical initial position; no pose edits after initialization.
    sim = scene.sim
    body = sim.model.body('black_pawn_d7').id
    address = sim.model.jnt_qposadr[sim.model.body_jntadr[body]]
    target = scene.feedback.endpoint_position('e3')
    sim.data.qpos[address:address+3] = [*target[:2], .019]
    mujoco.mj_forward(sim.model, sim.data)
    for _ in range(100):
        sim.advance(sim.target)
    scene.physical = PhysicalBoardState(scene.feedback.snapshot(0),
                                       position_tolerance_m=.003, angle_tolerance_rad=.15)
    result = scene.execute_request(plan(('e3','graveyard:slot_0'), ('e2','e3')))
    assert result['status'] == 'COMPLETED_SIMULATION_ORACLE', result['error_code']
    assert result['completed_transfers'] == 2
    assert scene.physical.confirmed.by_id['black_pawn_d7'].location == Location('graveyard', 'slot_0')
    assert scene.physical.confirmed.occupancy['e3'] == 'white_pawn_e2'
    assert scene.physical.confirmed.revision == 2
