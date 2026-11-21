from types import SimpleNamespace

import numpy as np
import pytest

from atom_mujoco.board_piece_localization import square_offsets, scene_square_offsets, registration_identity
from atom_mujoco.chess_commands import fen_occupancy


def frame(rgb, camera='side'):
    return SimpleNamespace(oriented=True, reference_sha256='layout', camera_id=camera,
                           rectified_rgb=rgb)


def test_board_localization_uses_rgb_translation_and_calibrated_axes():
    empty = np.zeros((800, 800, 3), dtype=np.uint8)
    reference = empty.copy()
    current = empty.copy()
    reference[635:660, 435:465] = 180
    current[632:657, 439:469] = 180
    offsets = square_offsets(frame(empty), frame(reference), frame(current), ['e2', 'f2'], .035)
    assert offsets == {'e2': pytest.approx([.0014, .00105])}
    assert not square_offsets(frame(empty), frame(reference), frame(current, 'other'), ['e2'], .035)


def test_logical_board_snapshot_preserves_piece_type_and_color():
    board = fen_occupancy('4k3/8/8/8/8/8/4P3/4K3 w - - 0 1')
    assert board == {'e8': 'k', 'e2': 'P', 'e1': 'K'}
    with pytest.raises(ValueError, match='eight files'):
        fen_occupancy('8/8/8/8/8/8/8/4K2 w - - 0 1')


def anchored_scene():
    empty = np.zeros((800, 800, 3), dtype=np.uint8)
    source = empty.copy()
    source[635:660, 435:465] = 180
    reference = frame(source)
    reference.homography = np.eye(3)
    scene = SimpleNamespace(empty_reference=frame(empty), pitch=.035,
        registration=dict(frame=reference, offsets={'e2': [.0007, -.00105]}, tolerance_m=.001))
    return scene, source


def test_anchored_translation_composes_camera_estimates_without_physics():
    scene, source = anchored_scene()
    shifted = np.zeros_like(source)
    shifted[633:658, 438:468] = 180
    observed = frame(shifted)
    observed.homography = np.eye(3)
    result = scene_square_offsets(scene, observed, ['e2'])
    assert result['e2'] == pytest.approx([.00175, -.00035])
    scene.sim = SimpleNamespace(qpos=np.full(30, 999.))
    assert scene_square_offsets(scene, observed, ['e2']) == result


@pytest.mark.parametrize('change', ['camera', 'board', 'missing_piece'])
def test_anchor_tracking_fails_closed_without_remembered_position_fallback(change):
    scene, source = anchored_scene()
    observed = frame(source.copy())
    observed.homography = np.eye(3)
    if change == 'camera':
        observed.camera_id = 'other'
    elif change == 'board':
        observed.homography[0, 2] = 10.
    else:
        observed.rectified_rgb[:] = 0
    assert scene_square_offsets(scene, observed, ['e2']) == {}


def test_registration_identity_binds_image_and_camera_origin_offsets():
    scene, _ = anchored_scene()
    original = registration_identity(scene)
    scene.registration['offsets']['e2'][0] += .001
    assert registration_identity(scene) != original
    assert registration_identity(SimpleNamespace()) is None
