"""P036 paired saved-image qualification using the actual native acvision executable."""
import argparse
import sys
from atom_mujoco.paths import MODULE_ROOT
sys.path.insert(0, str(MODULE_ROOT / "examples"))
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
from validate_native_perception.run import evaluate


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def identity(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=sha256(path))


def verify(configuration):
    if configuration.get('schema') != 1:
        raise ValueError('Unsupported configuration schema')
    frames = configuration['frames']
    if not frames or len({f['id'] for f in frames}) != len(frames):
        raise ValueError('Nonempty unique frame IDs required')
    artifacts = configuration['dependencies'] + [configuration['executable'], configuration['layout']]
    artifacts += [entry[key] for entry in frames for key in ('image', 'evaluator')]
    for artifact in artifacts:
        if sha256(artifact['path']) != artifact['sha256']:
            raise ValueError('Artifact changed: ' + artifact['path'])
    if configuration.get('methods') != ['checker', 'aruco']:
        raise ValueError('Expected paired native methods')
    for frame in frames:
        if Path(frame['id']).name != frame['id'] or frame['id'] in ('.', '..'):
            raise ValueError('Unsafe frame identifier')
        truth = read_json(frame['evaluator']['path'])
        if truth['image_sha256'] != frame['image']['sha256']:
            raise ValueError('Evaluator/image identity mismatch')
        points = np.asarray(truth['projected_centers_px'])
        canonical = np.asarray(truth['canonical_centers_px'])
        if (points.shape != (64, 2) or canonical.shape != (64, 2)
                or not np.isfinite(points).all() or not np.isfinite(canonical).all()
                or not np.isfinite(truth['square_pitch_m']) or truth['square_pitch_m'] <= 0):
            raise ValueError('Invalid independent evaluator points')
        if truth['squares'] != [f'{c}{r}' for r in range(1, 9) for c in 'abcdefgh']:
            raise ValueError('Unexpected evaluator ordering')


def configuration(source, bundle, layout, executable):
    source = Path(source).resolve(strict=True)
    report = read_json(source/'report.json')
    frames = []
    for record in report['results']:
        case = record['case']
        if Path(case).name != case:
            raise ValueError('Unsafe case identifier')
        frames.append(dict(id=case, image=identity(source/f'{case}.png'),
                           evaluator=identity(source/f'evaluator-only-{case}.json')))
    dependencies = [identity(path) for path in sorted(Path(bundle).resolve().rglob('*'))
                    if path.is_file()]
    dependencies += [identity(source/'report.json'), identity(Path(__file__)),
                     identity(Path(__file__).resolve().parents[1]/'validate_native_perception/run.py')]
    # Capture script and native dependencies are also part of replay provenance.
    dependencies += [identity(Path(__file__).resolve().parents[1]/'validate_board_reference/run.py')]
    dependencies += [identity(path) for path in sorted(Path(executable).resolve().parent.glob('*.dll'))]
    return dict(schema=1, source_report=report, frames=frames, dependencies=dependencies,
                executable=identity(executable), layout=identity(layout),
                methods=['checker', 'aruco'],
                evaluation='same D4 oracle-aligned geometry; named orientation separately',
                latency_scope='one subprocess including startup, decode, processing and export',
                repetitions=1, independence='static deterministic fixtures; no statistical trials')


def native_command(configuration, frame, method, output):
    if method not in configuration['methods']:
        raise ValueError('Unknown method')
    command = [configuration['executable']['path'], frame['image']['path'], str(output)]
    if method == 'aruco':
        command += ['--reference', configuration['layout']['path']]
    return command


def metrics(observation, truth):
    accepted = bool(observation.get('processing_completed') and
                    observation.get('homography') is not None)
    if observation.get('schema_version') != 2 or observation.get('implementation') != 'acvision_cpp':
        raise ValueError('Native schema 2 required')
    result = dict(accepted=accepted,
                  detected=observation.get('corners_px') is not None,
                  orientation=observation.get('orientation', 'unknown'),
                  orientation_status='unknown', unknown_squares=64,
                  named_correct=None, named_incorrect=None,
                  reference_residual_rectified_px=observation.get('reference_residual_rectified_px'),
                  errors=observation.get('errors', []), warnings=observation.get('warnings', []))
    if not accepted:
        result['geometry'] = None
        return result
    H = np.asarray(observation['homography'], dtype=float)
    if H.shape != (3, 3) or not np.isfinite(H).all() or np.linalg.det(H) == 0:
        raise ValueError('Invalid native homography')
    points = np.asarray(truth['projected_centers_px'])
    # Existing evaluator convention, shared by both methods.
    result['geometry'] = evaluate(observation, points, truth['square_pitch_m'],
                                  truth['candidate_truth_colors'])
    if result['orientation'] == 'a8_top_left_from_reference':
        mapped = np.column_stack((points, np.ones(64))) @ H.T
        mapped = mapped[:, :2]/mapped[:, 2:]
        expected = np.asarray(truth['canonical_centers_px'])
        correct = int(np.all(np.floor(mapped/100) == np.floor(expected/100), axis=1).sum())
        direct_mean = float(np.linalg.norm(mapped-expected, axis=1).mean())
        aligned_mean = result['geometry']['nominal_board_equivalent_error_mm']['mean'] / (
            truth['square_pitch_m']*10)
        orientation_status = 'correct' if np.isclose(direct_mean, aligned_mean, atol=1e-6) else 'incorrect'
        result.update(named_correct=correct, named_incorrect=64-correct, unknown_squares=0,
                      orientation_status=orientation_status)
    result['piece_localization_coverage'] = None
    return result


def summary(records):
    result = {}
    for method in ('checker', 'aruco'):
        group = [r for r in records if r['method'] == method]
        accepted = [r for r in group if r['metrics']['accepted']]
        latency = np.array([r['latency_ms'] for r in group])
        result[method] = dict(
            total=len(group), detected=sum(r['metrics']['detected'] for r in group),
            accepted=len(accepted), rejected=len(group)-len(accepted),
            orientation_known=sum(r['metrics']['orientation'] != 'unknown' for r in group),
            orientation_correct=sum(r['metrics']['orientation_status'] == 'correct' for r in group),
            orientation_incorrect=sum(r['metrics']['orientation_status'] == 'incorrect' for r in group),
            orientation_unknown=sum(r['metrics']['orientation_status'] == 'unknown' for r in group),
            named_correct=sum(r['metrics']['named_correct'] or 0 for r in group),
            named_incorrect=sum(r['metrics']['named_incorrect'] or 0 for r in group),
            unknown_squares=sum(r['metrics']['unknown_squares'] for r in group),
            geometry_correct=sum(round(r['metrics']['geometry']['square_assignment_accuracy']*64)
                                 for r in accepted),
            geometry_unknown_squares=64*(len(group)-len(accepted)),
            latency_ms=dict(mean=float(latency.mean()), median=float(np.median(latency)),
                            p95=float(np.percentile(latency, 95))),
            effective_sequential_fps=float(1000/latency.mean()),
            false_acceptance_rate=None, cpu_usage=None, grasp_error=None)
    return result


def markdown(result):
    lines = ['# P036 paired saved-image comparison', '',
             'Both methods process identical file bytes. Geometry uses the same',
             'oracle D4 alignment. Orientation and named addressing are separate.',
             'A rejected frame has unknown geometry and stays in denominators.', '',
             '| Method | Accepted / total | Geometry correct / all squares | Named correct | Named unknown | Mean process ms |',
             '|---|---:|---:|---:|---:|---:|']
    for method, value in result.items():
        lines.append(f"| {method} | {value['accepted']}/{value['total']} | "
                     f"{value['geometry_correct']}/{64*value['total']} | "
                     f"{value['named_correct']} | {value['unknown_squares']} | "
                     f"{value['latency_ms']['mean']:.2f} |")
    lines += ['', 'Geometry errors for accepted frames, rejection warnings, input identities,',
              'source hashes, overlays and timing are in metrics.json and manifest.json.',
              'Latency includes process startup and export. These static captures are',
              'one experimental sweep, without independent statistical repetitions.',
              'Mechanical acceptance thresholds, false-acceptance labels, physical grasp',
              'error, CPU usage and piece localization are unavailable in this scope.']
    return '\n'.join(lines) + '\n'


def run(config, output):
    verify(config)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'configuration.json', config)
    manifest = dict(schema=1, status='running', configuration_sha256=sha256(output/'configuration.json'),
                    python=sys.version, platform=platform.platform(),
                    versions={name: importlib.metadata.version(name) for name in ('numpy', 'mujoco', 'Pillow')},
                    invocation=sys.argv)
    records = []
    # Save enough state to diagnose an interrupted or failed run.
    write_json(output/'manifest.json', manifest)
    for frame in config['frames']:
        for method in config['methods']:
            destination = output/'native-observations'/frame['id']/method
            destination.parent.mkdir(parents=True, exist_ok=True)
            command = native_command(config, frame, method, destination)
            begin = time.perf_counter()
            completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
            elapsed = (time.perf_counter()-begin)*1000
            (destination.parent/f'{method}-stderr.txt').write_text(completed.stderr, encoding='utf-8')
            observation = read_json(destination/'observation.json')
            # Evaluator truth is first read after the native subprocess finishes.
            truth = read_json(frame['evaluator']['path'])
            measured = metrics(observation, truth)
            if completed.returncode != 0:
                measured.update(accepted=False, geometry=None, named_correct=None,
                                named_incorrect=None, unknown_squares=64)
            artifacts = [identity(p) for p in sorted(destination.iterdir()) if p.is_file()]
            records.append(dict(frame=frame['id'], method=method, image_sha256=frame['image']['sha256'],
                                returncode=completed.returncode, latency_ms=elapsed, metrics=measured,
                                source_sha256=observation.get('source_sha256'),
                                opencv_version=observation.get('opencv_version'),
                                command=command, artifacts=artifacts))
    verify(config)
    result = summary(records)
    write_json(output/'metrics.json', dict(schema=1, summary=result, frames=records))
    (output/'report.md').write_text(markdown(result), encoding='utf-8')
    write_json(output/'completion.json', dict(status='completed', inputs_verified=True,
               metrics_sha256=sha256(output/'metrics.json'), report_sha256=sha256(output/'report.md')))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--layout', type=Path)
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--replay', type=Path, help='Verified configuration.json from a previous run')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.replay:
        config = read_json(args.replay)
    else:
        if not all((args.source, args.bundle, args.layout, args.executable)):
            parser.error('Supply source, bundle, layout and executable or replay')
        config = configuration(args.source, args.bundle, args.layout, args.executable)
    print(json.dumps(run(config, args.output), indent=2))


if __name__ == '__main__':
    main()
