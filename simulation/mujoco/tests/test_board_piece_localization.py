from types import SimpleNamespace

import numpy as np
import pytest

from atom_mujoco.board_piece_localization import square_offsets
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
