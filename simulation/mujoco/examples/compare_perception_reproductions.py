"""Compare preserved P033/P034 captures with fresh qualification runs."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
from PIL import Image

from qualify_saved_perception import read_json, sha256, write_json


def compare(historical, current, reference):
    before = read_json(historical/'report.json')
    after = read_json(current/'report.json')
    if len(before['results']) != len(after['results']):
        raise ValueError('Capture count changed')
    frames = []
    for old, new in zip(before['results'], after['results']):
        if reference:
            case = new['case']
            if old['case'] != case:
                raise ValueError('Case order mismatch')
            image_name, directory = case+'.png', case
            keys = ['detected', 'orientation', 'mean_error_mm', 'max_error_mm', 'correct_squares']
        else:
            case = f"{new['azimuth']:g}-{abs(new['elevation'])}"
            if (old['azimuth'], old['elevation']) != (new['azimuth'], new['elevation']):
                raise ValueError('Camera order mismatch')
            image_name, directory = f'lateral-{case}.png', f'acvision-{case}'
            keys = ['status', 'square_assignment_accuracy',
                    'nominal_board_equivalent_error_mm', 'candidate_color_confusion']
        observation = read_json(current/directory/'observation.json')
        historical_obs = read_json(historical/directory/'observation.json')
        difference = np.abs(np.asarray(Image.open(historical/image_name)).astype(int) -
                            np.asarray(Image.open(current/image_name)).astype(int))
        overlays = {name: dict(path=str(current/directory/path),
                               sha256=sha256(current/directory/path)) if path else None
                    for name, path in observation['overlays'].items()}
        frames.append(dict(
            case=case, image_sha256=sha256(current/image_name),
            historical_image_sha256=sha256(historical/image_name),
            differing_pixels=int(np.any(difference, axis=2).sum()),
            max_channel_difference=int(difference.max()),
            comparable_metrics_equal=all(old.get(key) == new.get(key) for key in keys),
            historical_accepted=historical_obs['homography'] is not None,
            accepted=observation['homography'] is not None,
            board_detection_status=observation['board_detection_status'],
            orientation=observation['orientation'],
            reference_residual_rectified_px=observation.get('reference_residual_rectified_px'),
            warnings=observation['warnings'], errors=observation['errors'],
            overlays=overlays, source_sha256=observation['source_sha256'],
            opencv_version=observation['opencv_version'],
            archived_result=old, reproduced_result=new))
    fields = ['mujoco_version', 'image_size', 'executable_sha256', 'model_sha256',
              'source_model_sha256', 'layout_sha256']
    return dict(
        historical_directory=str(historical), current_directory=str(current),
        historical_report_sha256=sha256(historical/'report.json'),
        current_report_sha256=sha256(current/'report.json'),
        total=len(frames), historical_accepted=sum(f['historical_accepted'] for f in frames),
        accepted=sum(f['accepted'] for f in frames),
        rejected=sum(not f['accepted'] for f in frames),
        identical_pngs=sum(f['image_sha256'] == f['historical_image_sha256'] for f in frames),
        identical_decoded_images=sum(f['differing_pixels'] == 0 for f in frames),
        comparable_metrics_equal=sum(f['comparable_metrics_equal'] for f in frames),
        historical_runtime={key: before.get(key) for key in fields},
        current_runtime={key: after.get(key) for key in fields},
        latency_ms=None, latency_status='historical capture scripts have no per-frame timer',
        frames=frames)


def markdown(report):
    lines = ['# P036 historical reproduction report', '',
             '| Protocol | Historical accepted | Current accepted | Rejected | Equal metric records | Identical PNGs |',
             '|---|---:|---:|---:|---:|---:|']
    for name, record in report['reproductions'].items():
        total = record['total']
        lines.append(f"| {name} | {record['historical_accepted']}/{total} | "
                     f"{record['accepted']}/{total} | {record['rejected']} | "
                     f"{record['comparable_metrics_equal']}/{total} | {record['identical_pngs']}/{total} |")
    lines += ['', f"Protected files checked: {report['protected_files_checked']}.",
              f"Changed protected files: {len(report['protected_changes'])}.", '',
              'The JSON report records frame identities, pixel differences, overlays,',
              'warnings, source/runtime identities and archived/reproduced metrics.',
              'PNG identity differs for some renders, with a maximum observed channel',
              'difference of ' + str(max(f['max_channel_difference']
                                        for r in report['reproductions'].values()
                                        for f in r['frames'])) + '.',
              'The underlying cause of these rendering differences has not been isolated.',
              'The executable has evolved since the historical experiments.',
              'Model and layout identities are compared explicitly in the JSON.',
              'Capture-script latency was unmeasured historically and remains unavailable.',
              'Paired reprocessing latency is reported separately.',
              'P033 geometry uses oracle D4 alignment. P034 named addressing uses the',
              'configured marker orientation. Historical aggregates have different camera',
              'distance and resolution, so causal method comparisons use the paired study.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--p033', type=Path, required=True)
    parser.add_argument('--p034', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    audit = read_json(args.audit)
    protected_changes = [name for name, digest in audit['protected'].items()
                         if sha256(root/name) != digest]
    report = dict(
        schema=1,
        reproductions=dict(
            p033=compare(root/'simulation/mujoco/runs/p033-viewpoint-sweep-20261106',
                         args.p033.resolve(), False),
            p034=compare(root/'simulation/mujoco/runs/p034-markers-final',
                         args.p034.resolve(), True)),
        protected_files_checked=len(audit['protected']), protected_changes=protected_changes,
        audit_sha256=sha256(args.audit), python=sys.version, platform=platform.platform(),
        invocation=sys.argv,
        toolchain={name: subprocess.check_output(command, text=True).splitlines()[0]
                   for name, command in [('cmake', ['cmake', '--version']),
                                         ('git', ['git', '--version'])]})
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output/'metrics.json', report)
    (args.output/'report.md').write_text(markdown(report), encoding='utf-8')
    if protected_changes:
        raise RuntimeError('Protected inputs changed')
    print(args.output/'report.md')


if __name__ == '__main__':
    main()
