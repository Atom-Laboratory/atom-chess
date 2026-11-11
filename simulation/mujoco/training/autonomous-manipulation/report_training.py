"""Build a portable, read-only diagnostic report from autonomous run directories."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re

import numpy as np


RAW = ('steps.csv', 'decisions.jsonl', 'performance.csv', 'ppo_updates.csv',
       'network.csv', 'hardware.jsonl', 'baseline.json', 'report.json', 'failure.json', 'run.json')
PATH = re.compile(r'(?i)(?:[a-z]:[/\\\\]|/mnt/[a-z]/|/home/|/Users/)[^"\r\n\s<>]*')


def portable(text):
    return PATH.sub(lambda match: '<local-path-'+hashlib.sha256(
        match.group().encode('utf-8')).hexdigest()[:16]+'>', text)


def json_lines(path):
    if not path.exists():
        return []
    lines = path.read_text(encoding='utf-8').splitlines()
    records = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if index != len(lines)-1:
                raise
    return records


def summarize(run):
    def read(name):
        path = run/name
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    metadata = read('run.json')
    report = read('report.json')
    decisions = json_lines(run/'decisions.jsonl')
    hardware = json_lines(run/'hardware.jsonl')
    episodes = [row for row in decisions if row.get('success') or row.get('failure')
                or row.get('TimeLimit.truncated')]
    validation = Counter(row['validation']['status'] for row in decisions)
    components = Counter()
    events = Counter()
    for row in decisions:
        for name, value in row.get('reward_components', {}).items():
            components[name] += value
            events[name] += bool(value)
    action = np.asarray([row['action'] for row in decisions], dtype=float)
    timing = {key: sum(row.get('timings_s', {}).get(key, 0.) for row in decisions)
              for key in ('validation', 'physics', 'perception', 'feedback', 'total')}
    checkpoints = {}
    for archive in sorted(run.glob('*.zip')):
        sidecar = archive.with_suffix('.sha256')
        if sidecar.exists():
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            checkpoints[archive.name] = dict(sha256=digest, verified=digest == sidecar.read_text().strip())
    result = dict(run=run.name, status=report.get('status', 'error_recorded' if read('failure.json') else 'no_final_report'),
        environment_version=metadata.get('environment_version'), policy_version=metadata.get('policy_version'),
        algorithm='PPO' if metadata else None, seed=metadata.get('args', {}).get('seed'),
        steps=len(decisions), episodes=len(episodes), validation=dict(validation),
        accepted_fraction=validation['ACCEPTED']/len(decisions) if decisions else None,
        projected_accepted=sum(row['validation'].get('command_scale', 1.) < 1
                               for row in decisions if row['validation']['status']=='ACCEPTED'),
        terminations=dict(Counter(row.get('failure') or 'success' for row in episodes)),
        success_episodes=sum(bool(row.get('success')) for row in episodes),
        grasp_episodes=len({row['episode_index'] for row in decisions if row.get('bilateral_contact')}),
        lift_episodes=len({row['episode_index'] for row in decisions if row.get('lifted')}),
        unexpected_contact_steps=sum(bool(row.get('unexpected_contact')) for row in decisions),
        contact_steps=sum(bool(row.get('forbidden_contact')) for row in decisions),
        reward_totals=dict(components), reward_nonzero_steps=dict(events),
        action_mean=action.mean(axis=0).tolist() if action.size else None,
        action_std=action.std(axis=0).tolist() if action.size else None,
        action_saturation=(np.abs(action) >= .999).mean(axis=0).tolist() if action.size else None,
        summed_step_timing_s=timing,
        device=metadata.get('policy_device'), gpu=metadata.get('policy_gpu'),
        hardware_samples=len(hardware),
        hardware_medians={key: float(np.median([x[key] for x in hardware if x.get(key) is not None]))
                          for key in ('cpu_percent','gpu_utilization_percent','gpu_memory_mib','torch_reserved_bytes')
                          if any(x.get(key) is not None for x in hardware)},
        weights_changed=(report['weights_before'] != report['weights_after'] if 'weights_after' in report else None),
        training_wall_s=report.get('training_wall_s'), optimizer_wall_s=report.get('optimizer_wall_s'),
        evaluation={k:v for k,v in report.get('evaluation', {}).items() if k!='records'} or None,
        initial_evaluation={k:v for k,v in (report.get('baseline') or read('baseline.json')).items() if k!='records'} or None,
        checkpoints=checkpoints)
    return result, decisions, episodes, action


def plots(run, output, decisions, episodes, action, summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if episodes:
        fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout='constrained')
        x = np.arange(1, len(episodes)+1)
        axes[0,0].plot(x, [r['episode_return'] for r in episodes], label='return')
        window = min(5, len(x))
        axes[0,0].plot(x[window-1:], np.convolve([r['episode_return'] for r in episodes],
                            np.ones(window)/window, mode='valid'), label=f'{window}-episode mean')
        axes[0,0].legend()
        for key in ('success', 'bilateral_contact', 'lifted'):
            per_episode = {r['episode_index'] for r in decisions if r.get(key)}
            values = [float(r['episode_index'] in per_episode) for r in episodes]
            axes[0,1].plot(x[window-1:], np.convolve(values, np.ones(window)/window, mode='valid'), label=key)
        axes[0,1].set_ylim(-.05, 1.05)
        axes[0,1].legend()
        axes[1,0].plot(x, [r['episode_steps'] for r in episodes])
        axes[1,0].set_ylabel('Episode decisions')
        totals = summary['reward_totals']
        axes[1,1].barh(list(totals), list(totals.values()))
        axes[1,1].set_xlabel('Cumulative reward component')
        fig.suptitle('Training episodes')
        fig.savefig(output/'episodes.png', dpi=120)
        plt.close(fig)
    if action.size:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
        for axis, values in enumerate(action.T):
            axes[0].hist(values, bins=24, histtype='step', label=str(axis))
        axes[0].set_xlabel('Action sent to environment')
        axes[0].legend(title='Axis')
        validation = summary['validation']
        axes[1].barh(list(validation), list(validation.values()))
        axes[1].set_xlabel('Decisions')
        fig.savefig(output/'actions.png', dpi=120)
        plt.close(fig)
    updates = run/'ppo_updates.csv'
    if updates.exists():
        with updates.open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        fields = [key for key in ('policy_gradient_loss','value_loss','entropy_loss','approx_kl','explained_variance')
                  if any(row.get(key) for row in rows)]
        if fields:
            fig, axes = plt.subplots(len(fields), 1, figsize=(8, 2*len(fields)), layout='constrained', squeeze=False)
            for key, ax in zip(fields, axes[:,0]):
                values = [(int(row['training_step']), float(row[key])) for row in rows if row.get(key)]
                ax.plot(*zip(*values))
                ax.set_ylabel(key)
            axes[-1,0].set_xlabel('Training decisions')
            fig.savefig(output/'ppo.png', dpi=120)
            plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plots', action='store_true', help='Requires the diagnostics extra')
    parser.add_argument('runs', type=Path, nargs='+')
    args = parser.parse_args()
    if len({p.name for p in args.runs}) != len(args.runs) or any(not p.is_dir() for p in args.runs):
        parser.error('Provide existing run directories with distinct final directory names')
    args.output.mkdir(parents=True, exist_ok=False)
    inventory = []
    for run in args.runs:
        output = args.output/run.name
        output.mkdir()
        summary, decisions, episodes, action = summarize(run)
        inventory.append(summary)
        for name in RAW:
            path = run/name
            if path.exists():
                data = portable(path.read_text(encoding='utf-8')).encode('utf-8')
                (output/(name+'.gz')).write_bytes(gzip.compress(data, mtime=0))
        if args.plots:
            plots(run, output, decisions, episodes, action, summary)
    (args.output/'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    print(args.output/'inventory.json')


if __name__ == '__main__':
    main()
