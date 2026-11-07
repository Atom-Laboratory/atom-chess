"""P036 infrastructure regression tests. Native perception stays in C++."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

EXAMPLES = Path(__file__).resolve().parents[1]/'examples'
sys.path.insert(0, str(EXAMPLES))
from qualify_saved_perception import run as qualification


def truth():
    points = [[(c+.5)*100, (7-r+.5)*100] for r in range(8) for c in range(8)]
    return dict(projected_centers_px=points, canonical_centers_px=points,
                square_pitch_m=.035, candidate_truth_colors=['empty']*64,
                squares=[f'{c}{r}' for r in range(1, 9) for c in 'abcdefgh'])


def observation(accepted=True, oriented=False):
    return dict(schema_version=2, implementation='acvision_cpp', processing_completed=True,
                homography=np.eye(3).tolist() if accepted else None,
                corners_px=[[0, 0], [800, 0], [800, 800], [0, 800]] if accepted else None,
                orientation='a8_top_left_from_reference' if oriented else 'unknown',
                cells=[dict(row=r, column=c, candidate='empty') for r in range(8) for c in range(8)],
                warnings=[])


def record(method, accepted, oriented=False):
    return dict(method=method, latency_ms=100,
                metrics=qualification.metrics(observation(accepted, oriented), truth()))


def config(tmp_path):
    image = tmp_path/'image.png'
    image.write_bytes(b'identical-image-fixture')
    evaluator = tmp_path/'evaluator.json'
    value = truth()
    value['image_sha256'] = qualification.sha256(image)
    evaluator.write_text(json.dumps(value))
    exe = tmp_path/'native.exe'
    exe.write_bytes(b'fixture')
    layout = tmp_path/'layout.json'
    layout.write_text('{}')
    return dict(schema=1, dependencies=[], executable=qualification.identity(exe),
                layout=qualification.identity(layout), methods=['checker', 'aruco'],
                frames=[dict(id='frame', image=qualification.identity(image),
                             evaluator=qualification.identity(evaluator))])


def test_configuration_roundtrip_and_identity(tmp_path):
    value = config(tmp_path)
    path = tmp_path/'configuration.json'
    qualification.write_json(path, value)
    restored = qualification.read_json(path)
    assert restored == value
    qualification.verify(restored)
    with pytest.raises(FileExistsError):
        qualification.write_json(path, value)


@pytest.mark.parametrize('field', ['image', 'evaluator'])
def test_modified_artifacts_fail(tmp_path, field):
    value = config(tmp_path)
    Path(value['frames'][0][field]['path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='Artifact changed'):
        qualification.verify(value)


def test_evaluator_cannot_be_used_with_another_image(tmp_path):
    value = config(tmp_path)
    path = Path(value['frames'][0]['evaluator']['path'])
    data = qualification.read_json(path)
    data['image_sha256'] = 'incorrect'
    path.write_text(json.dumps(data))
    value['frames'][0]['evaluator'] = qualification.identity(path)
    with pytest.raises(ValueError, match='identity mismatch'):
        qualification.verify(value)


def test_native_boundary_has_only_image_output_layout(tmp_path):
    value = config(tmp_path)
    frame = value['frames'][0]
    output = tmp_path/'new-output'
    checker = qualification.native_command(value, frame, 'checker', output)
    aruco = qualification.native_command(value, frame, 'aruco', output)
    assert checker == [value['executable']['path'], frame['image']['path'], str(output)]
    assert aruco == checker + ['--reference', value['layout']['path']]
    assert frame['evaluator']['path'] not in aruco
    assert checker[1] == aruco[1]


def test_rejection_has_unknown_geometry_and_preserves_denominators():
    records = [record('checker', True), record('checker', False),
               record('aruco', True, True), record('aruco', False)]
    result = qualification.summary(records)
    assert result['checker']['total'] == 2
    assert result['checker']['accepted'] == 1
    assert result['checker']['rejected'] == 1
    assert result['checker']['geometry_correct'] == 64
    assert result['checker']['geometry_unknown_squares'] == 64
    assert result['checker']['unknown_squares'] == 128
    assert result['aruco']['unknown_squares'] == 64
    assert result['aruco']['orientation_correct'] == 1
    assert result['aruco']['orientation_unknown'] == 1
    rejected = records[1]['metrics']
    assert rejected['geometry'] is None


def test_geometry_and_orientation_are_separate():
    checker = qualification.metrics(observation(), truth())
    assert checker['geometry']['square_assignment_accuracy'] == 1
    assert checker['orientation_status'] == 'unknown'
    assert checker['named_correct'] is None
    wrong = observation(True, True)
    wrong['homography'] = [[-1, 0, 800], [0, 1, 0], [0, 0, 1]]
    result = qualification.metrics(wrong, truth())
    assert result['geometry']['square_assignment_accuracy'] == 1
    assert result['orientation_status'] == 'incorrect'
    assert result['named_correct'] == 0


def test_evaluation_does_not_modify_observation_or_truth():
    obs, expected = observation(True, True), truth()
    before = copy.deepcopy((obs, expected))
    qualification.metrics(obs, expected)
    assert (obs, expected) == before


def test_report_and_metrics_repeat_with_same_inputs():
    records = [record('checker', False), record('aruco', True, True)]
    first = qualification.summary(records)
    second = qualification.summary(copy.deepcopy(records))
    assert first == second
    assert qualification.markdown(first) == qualification.markdown(second)


def test_rejects_duplicate_and_unsafe_ids(tmp_path):
    value = config(tmp_path)
    value['frames'] *= 2
    with pytest.raises(ValueError, match='unique'):
        qualification.verify(value)
    value['frames'] = value['frames'][:1]
    value['frames'][0]['id'] = '..'
    with pytest.raises(ValueError, match='Unsafe'):
        qualification.verify(value)


def test_failed_run_preserves_existing_directory(tmp_path):
    value = config(tmp_path)
    output = tmp_path/'output'
    output.mkdir()
    sentinel = output/'preserve.txt'
    sentinel.write_text('existing')
    with pytest.raises(FileExistsError):
        qualification.run(value, output)
    assert sentinel.read_text() == 'existing'


@pytest.fixture
def measured_runs():
    import os
    value = os.environ.get('P036_RUN_ROOT')
    if not value:
        pytest.skip('Set P036_RUN_ROOT to validate measured artifacts')
    return Path(value)


def test_measured_replay_and_artifact_identity(measured_runs):
    first = qualification.read_json(measured_runs/'paired-final/metrics.json')
    replay = qualification.read_json(measured_runs/'paired-replay/metrics.json')
    config = qualification.read_json(measured_runs/'paired-final/configuration.json')
    qualification.verify(config)
    assert len(first['frames']) == len(replay['frames']) == 54
    assert [r['metrics'] for r in first['frames']] == [r['metrics'] for r in replay['frames']]
    assert [r['image_sha256'] for r in first['frames']] == [r['image_sha256'] for r in replay['frames']]
    for observation in first['frames'] + replay['frames']:
        for artifact in observation['artifacts']:
            assert qualification.sha256(artifact['path']) == artifact['sha256']
    for frame in config['frames']:
        rows = [r for r in first['frames'] if r['frame'] == frame['id']]
        assert len(rows) == 2
        assert rows[0]['image_sha256'] == rows[1]['image_sha256'] == frame['image']['sha256']


def test_protected_inputs_remain_identical(measured_runs):
    audit = qualification.read_json(measured_runs/'audit-before.json')
    root = Path(__file__).resolve().parents[3]
    assert audit['head'].startswith('dcf2dc1')
    for name, digest in audit['protected'].items():
        assert qualification.sha256(root/name) == digest


def test_historical_comparison_report_repeatable(measured_runs):
    from compare_perception_reproductions.run import compare_perception_reproductions as comparisons
    root = Path(__file__).resolve().parents[3]
    first = comparisons.compare(root/'simulation/mujoco/examples/validate_native_perception/runs/p033-viewpoint-sweep-20261106',
                                measured_runs/'p033-repeat', False)
    second = comparisons.compare(root/'simulation/mujoco/examples/validate_native_perception/runs/p033-viewpoint-sweep-20261106',
                                 measured_runs/'p033-repeat', False)
    assert first == second
    assert first['accepted'] == 2
    assert first['comparable_metrics_equal'] == 9
