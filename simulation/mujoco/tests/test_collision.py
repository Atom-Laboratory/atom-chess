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
    before = playground.sim.data.qpos.copy()
    result = playground.execute(operation='MOVE', source='e2', target='e3')
    assert result['collision_checked']
    assert not result['collision_report']['valid']
    assert 'COLLISION_PREFLIGHT_FAILED' in result['error_code']
    np.testing.assert_array_equal(playground.sim.data.qpos,before)
    assert playground.physical.confirmed.revision == 0
