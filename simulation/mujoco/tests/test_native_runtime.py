"""Native in-memory adapter and strict actor-input boundary."""
import ctypes
import json
import os
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image
import pytest

from atom_mujoco.native_vision import NativeVision
from atom_mujoco.camera_policy import policy_observation

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def library():
    value = os.environ.get('ACVISION_RUNTIME_DLL')
    if not value:
        pytest.skip('Build native runtime and set ACVISION_RUNTIME_DLL')
    return Path(value)


@pytest.fixture
def frame_rgb():
    path = Path(os.environ.get('ACVISION_TEST_IMAGE',
        str(ROOT/'simulation/mujoco/examples/compare_perception_reproductions/runs/p036/p034-repeat/initial-270-45.png')))
    if not path.is_file():
        pytest.skip('Set ACVISION_TEST_IMAGE to an RGB reference capture')
    return np.array(Image.open(path).convert('RGB'))


@pytest.fixture
def layout():
    return Path(os.environ.get('ACVISION_TEST_LAYOUT',
        str(ROOT/'docs/camera-rl/aruco-assets-v4/layout.json')))


def test_runtime_matches_native_cli(library, frame_rgb, layout, tmp_path):
    executable = Path(os.environ['ACVISION_PERCEPTION_EXE'])
    image = tmp_path/'input.png'
    Image.fromarray(frame_rgb).save(image)
    output = tmp_path/'offline'
    subprocess.run([str(executable), str(image), str(output), '--reference', str(layout)], check=True)
    offline = json.loads((output/'observation.json').read_text())
    original = frame_rgb.copy()
    with NativeVision(library, layout=layout) as vision:
        actual = vision.observe(frame_rgb)
        assert actual.oriented
        np.testing.assert_allclose(actual.homography, offline['homography'], atol=1e-12)
        np.testing.assert_array_equal(actual.rectified_rgb, np.array(Image.open(output/'rectified.png')))
        labels = {'empty': 0, 'white': 1, 'black': 2}
        assert actual.candidates.ravel().tolist() == [labels[c['candidate']] for c in offline['cells']]
    np.testing.assert_array_equal(original, frame_rgb)


def test_visibility_loss_clears_geometry_and_actor_input(library, frame_rgb, layout):
    with NativeVision(library, layout=layout) as vision:
        good = vision.observe(frame_rgb, captured_at_s=10)
        assert good.oriented
        missing = vision.observe(np.zeros_like(frame_rgb), captured_at_s=11)
        assert missing.homography is None
        assert not missing.oriented
        assert not missing.rectified_rgb.any()
        assert np.all(missing.candidates == -1)
        assert missing.foreground_centroids is None
        with pytest.raises(ValueError, match='BOARD_REFERENCE_UNAVAILABLE'):
            policy_observation(missing, source='e2', target='e4', previous_action=np.zeros(4),
                               commanded_joints=np.zeros(5), now_s=11)
        recovered = vision.observe(frame_rgb)
        assert recovered.oriented and recovered.sequence == 3


def test_background_loss_invalidates_previous_reference(library, frame_rgb, layout):
    with NativeVision(library, layout=layout) as vision:
        assert vision.set_empty(frame_rgb)
        current = vision.observe(frame_rgb)
        assert current.foreground_centroids is not None
        assert np.isnan(current.foreground_centroids).all()
        assert not vision.set_empty(np.zeros_like(frame_rgb))
        assert vision.observe(frame_rgb).foreground_centroids is None


def test_buffer_validation_close_and_contexts(library, frame_rgb, layout):
    first = NativeVision(library, layout=layout)
    with NativeVision(library, layout=layout) as second:
        assert first.observe(frame_rgb).sequence == second.observe(frame_rgb).sequence == 1
        first.close()
        first.close()
        assert second.observe(frame_rgb).sequence == 2
        with pytest.raises(RuntimeError, match='closed'):
            first.observe(frame_rgb)
        for invalid in [frame_rgb.astype(float), frame_rgb[:, ::2], frame_rgb[:, :, 0]]:
            with pytest.raises(ValueError, match='contiguous'):
                second.observe(invalid)


def test_policy_inputs_have_only_declared_observable_features(library, frame_rgb, layout):
    with NativeVision(library, layout=layout) as vision:
        frame = vision.observe(frame_rgb, captured_at_s=20)
        kwargs = dict(source='e2', target='e4', previous_action=np.zeros(4),
                      commanded_joints=np.array([0, .12, 0, 0, 0]), now_s=20.1)
        first = policy_observation(frame, **kwargs)
        # Hidden simulator/reward state has no input parameter in this boundary.
        with pytest.raises(TypeError):
            policy_observation(frame, simulator_truth={'piece_position': [1, 2, 3]}, **kwargs)
        second = policy_observation(frame, **kwargs)
        assert set(first.features()) == {'image', 'task', 'previous_action', 'commanded_joints', 'phase'}
        for name in first.features():
            np.testing.assert_array_equal(first.features()[name], second.features()[name])
        assert first.image_chw.shape == (3, 96, 96)
        np.testing.assert_allclose(first.task, np.array([4, 6, 4, 4])/7)
        with pytest.raises(ValueError):
            first.image_chw.setflags(write=True)
        with pytest.raises(ValueError):
            frame.raw_rgb.setflags(write=True)


def test_actor_rejects_stale_future_and_malformed_tasks(library, frame_rgb, layout):
    with NativeVision(library, layout=layout) as vision:
        frame = vision.observe(frame_rgb, captured_at_s=20)
        kwargs = dict(source='e2', target='e4', previous_action=np.zeros(4),
                      commanded_joints=np.zeros(5))
        for now in (19, 21):
            with pytest.raises(ValueError, match='STALE_OR_FUTURE_FRAME'):
                policy_observation(frame, now_s=now, **kwargs)
        for source in ('a0', 'e9', 'e4'):
            with pytest.raises(ValueError):
                policy_observation(frame, now_s=20, **dict(kwargs, source=source))
        with pytest.raises(ValueError):
            policy_observation(frame, now_s=20, **dict(kwargs, previous_action=np.ones(4)*2))


def test_native_bad_buffer_does_not_reuse_output(library, frame_rgb, layout):
    # Exercise the C ABI directly, including its failure path.
    from atom_mujoco.native_vision import _Frame
    with NativeVision(library, layout=layout) as vision:
        output = _Frame()
        output.board_valid = 1
        rgb = np.ones((800, 800, 3), dtype=np.uint8)
        ptr = rgb.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        status = vision._native.acvision_runtime_process(
            vision._context, ptr, 1, 800, 800, ctypes.byref(output), ptr, rgb.nbytes)
        assert status == -1
        assert output.board_valid == 0
        assert all(c == -1 for c in output.candidates)
        assert not rgb.any()
