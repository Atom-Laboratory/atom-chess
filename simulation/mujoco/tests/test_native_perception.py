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
    assert subprocess.run([executable,str(tmp_path/'missing.png'),str(tmp_path/'missing-out')]).returncode == 2
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
    assert result['processing_completed'] and not result['perception_valid']


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
    assert result['schema_version'] == 2 and len(result['source_sha256']) == 64
    assert result['image_id'].startswith('fnv1a64:')
    assert result['configuration_id'] == 'acvision-defaults-800-v1'
    assert len(result['cells']) == 64
    assert result['orientation'] == 'unknown' and not result['motion_ready']
    assert all(c['confidence'] is None and c['square'] is None for c in result['cells'])
    corners = np.array(result['corners_px'])
    mapped = np.column_stack((corners,np.ones(4))) @ np.array(result['homography']).T
    np.testing.assert_allclose(mapped[:,:2]/mapped[:,2:],[[0,0],[800,0],[800,800],[0,800]],atol=.001)
    assert Image.open(out/'rectified-grid.png').size == (800,800)
    assert Image.open(out/'rectified.png').size == (800,800)
    assert all((out/p).is_file() for p in result['overlays'].values())
    assert result['homography_geometry']['direction'] == 'original_image_to_rectified'


@pytest.mark.parametrize('kind,code',[
    ('empty','EMPTY_IMAGE_FILE'),('garbage','EMPTY_OR_UNDECODABLE_IMAGE'),
    ('small','INVALID_DIMENSIONS'),('gray','UNSUPPORTED_CHANNELS'),
    ('rgba','UNSUPPORTED_CHANNELS'),('config','INVALID_CONFIGURATION')])
def test_rejected_inputs_have_failure_records(executable,tmp_path,kind,code):
    image = tmp_path/'input.png'
    if kind == 'empty': image.write_bytes(b'')
    elif kind == 'garbage': image.write_bytes(b'not an image')
    else:
        shape = (20,20,3) if kind == 'small' else (100,100,4) if kind == 'rgba' else (100,100) if kind == 'gray' else (100,100,3)
        Image.fromarray(np.zeros(shape,dtype=np.uint8)).save(image)
    out = tmp_path/'failure'
    extra = ['--config','invented-config'] if kind == 'config' else []
    process = subprocess.run([executable,str(image),str(out),*extra])
    assert process.returncode == 2
    result = json.loads((out/'observation.json').read_text())
    assert result['errors'][0]['code'] == code
    assert not result['processing_completed'] and not result['perception_valid']
    assert all(p is None for p in result['overlays'].values())
    assert not result['cells']


@pytest.mark.parametrize('kind',['rectangle','sheet','table','cropped_board'])
def test_negative_scenes_report_candidates_not_success(executable,tmp_path,kind):
    from PIL import ImageDraw
    frame = Image.new('RGB',(600,600),(50,70,90))
    draw = ImageDraw.Draw(frame)
    if kind == 'rectangle': draw.rectangle((100,100,500,500),fill='white',outline='black',width=8)
    elif kind == 'sheet': draw.polygon([(100,100),(480,80),(520,490),(70,520)],fill=(240,240,230))
    elif kind == 'table':
        draw.rectangle((50,200,550,400),fill=(160,100,60))
        draw.rectangle((60,400,90,599),fill=(120,70,40))
        draw.rectangle((510,400,540,599),fill=(120,70,40))
    else:
        for r in range(8):
            for c in range(8):
                draw.rectangle((c*80-80,r*80-100,c*80,r*80-20),fill='white' if (r+c)%2 else 'black')
    image = tmp_path/f'{kind}.png'
    frame.save(image)
    out = tmp_path/'result'
    subprocess.run([executable,str(image),str(out)],check=True)
    result = json.loads((out/'observation.json').read_text())
    assert result['processing_completed'] and not result['perception_valid']
    assert 'RECTANGLE_FALSE_POSITIVES_POSSIBLE' in result['warnings']
    assert all(c['occupancy']=='unknown' and c['square'] is None for c in result['cells'])
    # A rectangle false positive is measured, not fixed by this integration.
    if kind in ('rectangle','sheet'):
        assert result['board_detection_status'] == 'unvalidated_candidate'
    if result['homography'] is None:
        assert result['overlays']['rectified_grid'] is None


def test_bgr_boundary_roundtrip_and_determinism(executable,tmp_path):
    pixels = np.zeros((100,100,3),dtype=np.uint8)
    pixels[:]=[220,30,5]  # RGB file. Decoder must not swap the saved overlay colors.
    image = tmp_path/'colors.png'
    Image.fromarray(pixels).save(image)
    results=[]
    for name in ('first','second'):
        out=tmp_path/name
        subprocess.run([executable,str(image),str(out),'--config','acvision-defaults-800-v1'],check=True)
        np.testing.assert_array_equal(np.array(Image.open(out/'corners.png')),pixels)
        results.append((out/'observation.json').read_bytes())
    assert results[0] == results[1]


def test_same_image_is_independent_of_changed_simulator(executable,tmp_path):
    from atom_mujoco.backend import Simulation
    bundle=Path(__file__).resolve().parents[1]/'runs/playground-fingertip-only-v1'
    if not bundle.exists(): pytest.skip('Requires existing simulation fixture')
    sim=Simulation(bundle)
    image=tmp_path/'fixed.png'
    Image.new('RGB',(100,100),(20,40,60)).save(image)
    args=[executable,str(image)]  # Only image and output go across the boundary.
    subprocess.run([*args,str(tmp_path/'before')],check=True)
    sim.data.qpos[:] += .123
    subprocess.run([*args,str(tmp_path/'after')],check=True)
    assert (tmp_path/'before/observation.json').read_bytes() == (tmp_path/'after/observation.json').read_bytes()


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
