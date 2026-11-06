"""Native adapter integration tests. Set ACVISION_PERCEPTION_EXE after building."""
import json
import os
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image
import pytest


@pytest.fixture
def executable():
    value = os.environ.get('ACVISION_PERCEPTION_EXE')
    if not value:
        pytest.skip('Build acvision perception_image and set ACVISION_PERCEPTION_EXE')
    path = Path(value)
    assert path.is_file()
    return str(path)


def test_missing_image_and_preserved_output(executable,tmp_path):
    assert subprocess.run([executable,str(tmp_path/'missing.png'),str(tmp_path/'out')]).returncode == 2
    image = tmp_path/'blank.png'
    Image.fromarray(np.zeros((600,800,3),dtype=np.uint8)).save(image)
    out = tmp_path/'out'
    subprocess.run([executable,str(image),str(out)],check=True)
    original = (out/'observation.json').read_bytes()
    assert subprocess.run([executable,str(image),str(out)]).returncode == 2
    assert (out/'observation.json').read_bytes() == original
    result = json.loads(original)
    assert result['homography'] is None and result['cells'] == []
    assert result['motion_ready'] is False


def test_grid_and_homography_contract(executable,tmp_path):
    board = np.full((600,600,3),127,dtype=np.uint8)
    for row in range(8):
        for col in range(8):
            board[100+row*50:150+row*50,100+col*50:150+col*50] = 255*((row+col)%2)
    image = tmp_path/'board.png'
    Image.fromarray(board).save(image)
    out = tmp_path/'detected'
    subprocess.run([executable,str(image),str(out)],check=True)
    result = json.loads((out/'observation.json').read_text())
    assert result['implementation'] == 'acvision_cpp'
    assert len(result['cells']) == 64
    assert result['orientation'] == 'unknown' and not result['motion_ready']
    assert all(c['confidence'] is None and c['square'] is None for c in result['cells'])
    corners = np.array(result['corners_px'])
    mapped = np.column_stack((corners,np.ones(4))) @ np.array(result['homography']).T
    np.testing.assert_allclose(mapped[:,:2]/mapped[:,2:],[[0,0],[800,0],[800,800],[0,800]],atol=.001)
    assert Image.open(out/'rectified-grid.png').size == (800,800)


def test_evaluator_projection_and_identity_mapping():
    import importlib.util
    from types import SimpleNamespace
    path = Path(__file__).resolve().parents[1]/'examples/validate_native_perception.py'
    spec = importlib.util.spec_from_file_location('native_evaluator',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    camera = SimpleNamespace(pos=np.array([0.,0.,1.]),forward=np.array([0.,0.,-1.]),
                             up=np.array([0.,1.,0.]),frustum_near=.1,
                             frustum_top=.1,frustum_bottom=-.1)
    points = np.array([[0,0,0],[.5,0,0],[0,.5,0]])
    np.testing.assert_allclose(module.project(points,[camera,camera],800,600),
                               [[400,300],[550,300],[400,150]])
    centers = np.array([(c+.5,r+.5) for r in range(8) for c in range(8)])*100
    result = module.evaluate({'homography':np.eye(3).tolist()},centers,.035)
    assert result['square_assignment_accuracy'] == 1.
    assert result['nominal_board_equivalent_error_mm']['max'] == 0.
    assert result['orientation_estimated_by_vision'] is False
    assert not result['motion_ready']
