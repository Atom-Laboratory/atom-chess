"""Unsmoothed BC/PPO macro-policy metrics and paired CPU execution durations."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    bc, updates, episodes, sources, reports = [], [], [], {}, []
    for run in args.runs:
        for name in ('report.json', 'bc-metrics.csv', 'training-metrics.csv', 'episodes.csv'):
            path = run / name
            if path.exists():
                sources[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
        if (run / 'bc-metrics.csv').exists():
            bc.extend(rows(run / 'bc-metrics.csv'))
        updates.extend(rows(run / 'training-metrics.csv'))
        episodes.extend(rows(run / 'episodes.csv'))
        reports.append(json.loads((run / 'report.json').read_text()))
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
    ax = axes[0, 0]
    ax.plot([int(r['epoch']) for r in bc], [max(float(r['actor_latent_mse']), 1e-12) for r in bc], color='#006c76')
    ax.set(yscale='log', xlabel='BC optimizer epoch', ylabel='Actor latent MSE', title='A. Expert mean warm-start')
    ax = axes[0, 1]
    x = [int(r['update']) for r in updates]
    line1, = ax.plot(x, [float(r['value_loss']) for r in updates], 'o-', label='Value MSE', color='#a63446')
    ax.set(xlabel='PPO update', ylabel='Value MSE', title='B. Shared-policy optimizer metrics')
    other = ax.twinx()
    line2, = other.plot(x, [float(r['policy_loss']) for r in updates], 's--', color='#155f8b', label='Clipped policy loss')
    other.set_ylabel('Clipped policy loss')
    ax.legend(handles=[line1, line2], loc='best', fontsize=8)
    ax = axes[1, 0]
    ax.scatter(np.arange(1, len(episodes) + 1), [float(r['reward']) for r in episodes],
        c=[int(r['update']) for r in episodes], cmap='viridis', s=24)
    ax.set(xlabel='Completed training macro episodes', ylabel='Physical macro reward', title='C. Raw episodes; one training entry')
    ax = axes[1, 1]
    names, train, validation = ['BC mean'], [reports[0]['before'][0]['duration_s']], [reports[0]['before'][1]['duration_s']]
    for report in reports:
        names.append(f"PPO update {report['completed_updates']}")
        train.append(report['after'][0]['duration_s']); validation.append(report['after'][1]['duration_s'])
    positions = np.arange(len(names))
    ax.bar(positions - .18, train, .36, label='Training entry', color='#006c76')
    ax.bar(positions + .18, validation, .36, label='Excluded validation entry', color='#b86421')
    ax.set(xticks=positions, xticklabels=names, ylabel='Simulated Stage A duration (s)', title='D. CPU-verified deterministic commands')
    ax.legend(fontsize=8)
    for axis in axes.flat:
        axis.grid(axis='y', alpha=.2)
    fig.suptitle('Isolated camera-feature parameter policy — tiny integration pilot', fontsize=14)
    for extension in ('svg', 'pdf', 'png'):
        fig.savefig(args.output / ('FIG-0004-stage-a-policy.' + extension), dpi=180)
    vector = args.output / 'FIG-0004-stage-a-policy.svg'
    vector.write_text('\n'.join(line.rstrip() for line in vector.read_text(encoding='utf-8').splitlines()) + '\n', encoding='utf-8')
    plt.close(fig)
    (args.output / 'figure-provenance.json').write_text(json.dumps(dict(schema=1, figure='FIG-0004', sources=sources,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), smoothing=False,
        scope='one training entry; one excluded validation entry; no independent reliability claim or error bars'), indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
