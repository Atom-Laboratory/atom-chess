import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demonstrations import actor_observation, intervals, validate_actor, load_candidate


def test_actor_allowlist_uses_issued_commands_and_rejects_truth():
    issued = np.arange(6.)
    row = actor_observation(np.zeros((96, 96, 3), dtype=np.uint8), issued, [.2, -.1], 'e2', 'e4', 'CLOSE')
    issued[:] = 100.  # A mutable physics/controller buffer cannot change the captured observation.
    np.testing.assert_array_equal(row['issued_command'], np.arange(6.))
    actor = {k: v[None, ...] for k, v in row.items()}
    validate_actor(actor, 1, 6)
    for field in ('qpos', 'object_position', 'contacts', 'lift_success', 'qvel'):
        with pytest.raises(ValueError, match='allowlist'):
            validate_actor(dict(actor, **{field: np.zeros((1, 1))}), 1, 6)
    np.testing.assert_array_equal(actor['phase'], [[1., 0., 0., 0.]])


def test_pre_action_intervals_are_disjoint_and_preserve_short_last_chunk():
    assert intervals(105, 50) == [(0, 50), (50, 100), (100, 105)]
    with pytest.raises(ValueError):
        intervals(105, 0)
    with pytest.raises(ValueError):
        intervals(20001, 50)


def test_candidate_rejects_failed_report_before_loading_physics(tmp_path):
    (tmp_path / 'report.json').write_text('{"status":"FROZEN_CANDIDATE_EVALUATION_FAILED"}')
    with pytest.raises(ValueError, match='verified candidate'):
        load_candidate(tmp_path, None, None, tmp_path)
