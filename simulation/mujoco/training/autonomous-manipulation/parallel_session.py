"""Bounded background PPO comparisons, with measured 2/4/8-process escalation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    temporary = path.with_suffix('.next.json')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def choose_best(results):
    completed = [r for r in results if r.get('status') == 'completed']
    if not completed:
        return None
    return max(completed, key=lambda r: (r['success_rate'], r['mean_return']))


def next_workers(current, success_rate, memory_ok, *, throughput=None, previous=None, previous_workers=None):
    if (previous_workers is not None and previous_workers < current and previous is not None
            and throughput is not None and throughput < .9*previous):
        return previous_workers, 'aggregate throughput decreased by more than 10%'
    if success_rate >= .5 and memory_ok and current < 8:
        return current*2, 'selection success >= 50% and projected memory fits'
    return current, 'keep current concurrency; qualification/resource gate not passed'


def worker_arguments(config, output, source, *, steps, seed, threads, checkpoint=None):
    return [sys.executable, '-u', '-B', str(Path(__file__).with_name('run.py')),
        '--config', str(config), '--output', str(output),
        *(['--warm-start-checkpoint', str(checkpoint)] if checkpoint else ['--warm-start', str(source)]),
        '--objective', 'grasp', '--steps', str(steps), '--horizon', '128', '--episodes', '8',
        '--evaluation-seed', '930000', '--seed', str(seed), '--rollout-steps', '128',
        '--batch-size', '64', '--epochs', '5', '--checkpoint-every', '1024',
        '--ent-coef', '.01', '--device', 'cuda', '--headless', '--torch-threads', str(threads)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--initial-checkpoints', type=Path, nargs=2,
                        help='Two hash-verified checkpoints to recover the first round, one per worker')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--chunk-steps', type=int, default=8192)
    parser.add_argument('--total-steps', type=int, default=131072, help='Aggregate additional training decisions')
    args = parser.parse_args()
    if args.chunk_steps < 128 or args.chunk_steps % 128 or args.total_steps < 256 or args.total_steps % 128:
        parser.error('Use positive complete 128-step rollouts and a budget for at least two workers')
    config, source = args.config.resolve(strict=True), args.source_run.resolve(strict=True)
    pilot = read(source/'report.json')
    if pilot.get('status') != 'completed' or not pilot.get('checkpoint_reload_verified'):
        parser.error('A completed, reload-verified source policy is required')
    if hashlib.sha256((source/'policy.zip').read_bytes()).hexdigest() != pilot['checkpoint_sha256']:
        parser.error('Source checkpoint hash differs')
    checkpoints = [path.resolve(strict=True) for path in args.initial_checkpoints or []]
    for checkpoint in checkpoints:
        expected = checkpoint.with_suffix('.sha256').read_text().strip()
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != expected:
            parser.error('Recovery checkpoint hash differs')
        read(checkpoint.parent/'run.json')
    import psutil
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA required; no silent CPU fallback')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'logs').mkdir()
    state = dict(schema=1, status='running', pid=os.getpid(), objective='grasp',
        process_create_time=psutil.Process(os.getpid()).create_time(), heartbeat_unix_s=time.time(),
        scope='experimental independent autonomous policies; not qualified hybrid control',
        config=str(config), source_run=str(source), total_budget=args.total_steps,
        initial_checkpoints=[str(path) for path in checkpoints],
        config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        gpu=torch.cuda.get_device_name(), stage_workers=2, consumed_steps=0, rounds=[],
        escalation='50% success on 8 selection episodes, memory headroom and measured throughput',
        evaluation_note='Repeated selection seeds are validation, not an untouched final test set')
    write(output/'session.json', state)
    (output/'README.md').write_text(
        '# Experimental parallel camera-actor PPO\n\n'
        'Read `session.json` for live round/worker paths and status. Each worker has its own '
        'policy, checkpoints, CSVs and evaluation. Logs are in `logs/`. Policies are not merged. '
        'The initial two workers can increase to four and eight only after validation/resource gates. '
        'No hardware qualification or successful learning is implied.\n\n'
        'Create a file named `STOP` in this directory to stop after the active round completes. '
        'Deleting/closing a viewer does not stop headless jobs. The aggregate step budget is finite.\n', encoding='utf-8')
    workers, round_id, previous_fps, previous_workers, capacity_cap = 2, 0, None, None, 8
    try:
        while state['consumed_steps']+128*workers <= args.total_steps and not (output/'STOP').exists():
            round_id += 1
            remaining = args.total_steps-state['consumed_steps']
            per_worker = min(args.chunk_steps, (remaining//workers//128)*128)
            if previous_workers is not None and workers > previous_workers:
                per_worker = min(per_worker, 2048)  # Bounded capacity comparison before a larger chunk.
            folder = output/f'round-{round_id:02d}'
            folder.mkdir()
            event = dict(round=round_id, workers=workers, steps_each=per_worker,
                         source=str(source), status='running', jobs=[])
            state['rounds'].append(event)
            start = time.monotonic()
            idle_free, gpu_total = torch.cuda.mem_get_info()
            peak_gpu_used, peak_rss = gpu_total-idle_free, 0
            jobs = []
            threads = max(1, min(2, (os.cpu_count() or 2)//(2*workers)))
            for index in range(workers):
                seed = 7+round_id*1000+index*37
                directory = folder/f'seed-{seed}'
                stdout = (output/'logs'/f'round-{round_id:02d}-seed-{seed}.stdout.log').open('x', encoding='utf-8')
                stderr = (output/'logs'/f'round-{round_id:02d}-seed-{seed}.stderr.log').open('x', encoding='utf-8')
                command = worker_arguments(config, directory, source, steps=per_worker, seed=seed, threads=threads)
                if round_id == 1 and checkpoints:
                    command = worker_arguments(config, directory, source, steps=per_worker, seed=seed,
                                               threads=threads, checkpoint=checkpoints[index])
                process = subprocess.Popen(command, cwd=Path.cwd(), stdout=stdout, stderr=stderr,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                jobs.append((process, directory, stdout, stderr))
                event['jobs'].append(dict(pid=process.pid, directory=str(directory), seed=seed, command=command))
            write(output/'session.json', state)
            while any(p.poll() is None for p, _, _, _ in jobs):
                free, _ = torch.cuda.mem_get_info()
                peak_gpu_used = max(peak_gpu_used, gpu_total-free)
                rss = 0
                for p, _, _, _ in jobs:
                    try:
                        root = psutil.Process(p.pid)
                        rss += sum(child.memory_info().rss for child in [root, *root.children(recursive=True)])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                peak_rss = max(peak_rss, rss)
                event.update(elapsed_s=time.monotonic()-start, peak_gpu_used_bytes=peak_gpu_used,
                             peak_process_rss_bytes=peak_rss)
                state['heartbeat_unix_s'] = time.time()
                write(output/'session.json', state)
                time.sleep(10)
            results = []
            for process, directory, stdout, stderr in jobs:
                stdout.close()
                stderr.close()
                if process.returncode != 0 or not (directory/'report.json').exists():
                    results.append(dict(directory=str(directory), status='failed', exit_code=process.returncode))
                    continue
                report = read(directory/'report.json')
                records = report['evaluation']['records']
                results.append(dict(directory=str(directory), status=report['status'],
                    success_rate=report['evaluation']['success_rate'],
                    mean_return=sum(r['episode_return'] for r in records)/len(records), steps=report['steps']))
            event.update(status='completed', results=results, elapsed_s=time.monotonic()-start)
            state['consumed_steps'] += sum(r.get('steps', 0) for r in results)
            best = choose_best(results)
            if best is None or any(r['status'] != 'completed' for r in results):
                state['status'] = 'worker_failure'
                break
            source = Path(best['directory'])
            state['best_run'] = str(source)
            fps = (sum(r['steps'] for r in results)/event['elapsed_s']
                   if event['elapsed_s'] > 0 else None)
            per_worker_gpu = max(0, peak_gpu_used-(gpu_total-idle_free))/workers
            desired = min(workers*2, 8)
            memory_ok = (fps is not None and per_worker_gpu*desired*1.25 < idle_free*.8
                         and peak_rss/workers*desired < psutil.virtual_memory().available*.8)
            next_count, reason = next_workers(workers, best['success_rate'], memory_ok,
                throughput=fps, previous=previous_fps, previous_workers=previous_workers)
            if next_count < workers:
                capacity_cap = next_count
            next_count = min(next_count, capacity_cap)
            event.update(aggregate_decisions_per_wall_s=fps, next_workers=next_count, decision=reason,
                         selection_success_rate=best['success_rate'], memory_gate=memory_ok)
            previous_fps, previous_workers, workers = fps, workers, next_count
            state['stage_workers'] = workers
            write(output/'session.json', state)
        if state['status'] == 'running':
            state['status'] = 'stopped_after_round' if (output/'STOP').exists() else 'budget_complete'
    except Exception as error:
        state.update(status='session_failure', error=repr(error))
        raise
    finally:
        write(output/'session.json', state)


if __name__ == '__main__':
    main()
