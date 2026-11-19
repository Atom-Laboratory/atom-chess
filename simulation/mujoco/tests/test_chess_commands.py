import pytest
import os
from pathlib import Path

pytestmark = pytest.mark.skipif(
    not os.environ.get("ATOM_CHESS_BRIDGE") and not (Path(__file__).resolve().parents[3] / "build/chess-ui/software/integration/chess_move_request").is_file(),
    reason="Build chess_move_request or configure ATOM_CHESS_BRIDGE for real C++ tests")
from atom_mujoco.chess_commands import plan_move


def test_real_core_validates_and_decomposes_capture():
    # Requires the compiled chess_move_request executable. This calls real C++.
    result = plan_move(['e2e4', 'd7d5'], 'e4d5')
    assert result['steps'] == [dict(source='d5', target='home'),
                               dict(source='e4', target='d5')]
    with pytest.raises(ValueError, match='Illegal move'):
        plan_move([], 'e2e5')


def test_real_core_orders_castling_rook():
    history = ['e2e4','e7e5','g1f3','b8c6','f1c4','g8f6']
    result = plan_move(history,'e1g1')
    assert result['steps'] == [dict(source='e1',target='g1'),dict(source='h1',target='f1')]
