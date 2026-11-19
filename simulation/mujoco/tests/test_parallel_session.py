import importlib.util
from pathlib import Path


def module():
    path = Path(__file__).resolve().parents[1]/'training/autonomous-manipulation/parallel_session.py'
    spec = importlib.util.spec_from_file_location('parallel_session', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_scale_requires_selection_success_and_resources():
    session = module()
    assert session.next_workers(2, .49, True)[0] == 2
    assert session.next_workers(2, .5, False)[0] == 2
    assert session.next_workers(2, .5, True)[0] == 4
    assert session.next_workers(4, .5, True)[0] == 8
    assert session.next_workers(8, 1., True)[0] == 8
    assert session.next_workers(4, 1., True, throughput=8., previous=10., previous_workers=2)[0] == 2


def test_best_policy_uses_success_before_validation_return():
    best = module().choose_best([
        dict(status='failed', success_rate=1., mean_return=100.),
        dict(status='completed', success_rate=.25, mean_return=10.),
        dict(status='completed', success_rate=.5, mean_return=-1.),
    ])
    assert best['success_rate'] == .5


def test_workers_are_headless_cuda_and_have_separate_seed_and_output():
    session = module()
    a = session.worker_arguments('cfg.json', 'run-a', 'pilot', steps=8192, seed=7, threads=2)
    b = session.worker_arguments('cfg.json', 'run-b', 'pilot', steps=8192, seed=44, threads=2)
    assert '--headless' in a and a[a.index('--device')+1] == 'cuda'
    assert a[a.index('--objective')+1] == 'grasp'
    assert a[a.index('--output')+1] != b[b.index('--output')+1]
    assert a[a.index('--seed')+1] != b[b.index('--seed')+1]
    recovered = session.worker_arguments('cfg.json', 'recovered', 'pilot', steps=8192,
        seed=7, threads=2, checkpoint=Path('previous/checkpoint-2048.zip'))
    assert '--warm-start-checkpoint' in recovered and '--warm-start' not in recovered


def test_bounded_session_consumes_real_report_schema(monkeypatch, tmp_path):
    import hashlib
    import json
    import sys
    from types import SimpleNamespace

    session = module()
    source = tmp_path/'source'
    source.mkdir()
    (source/'policy.zip').write_bytes(b'synthetic-policy-fixture')
    (source/'report.json').write_text(json.dumps(dict(status='completed', checkpoint_reload_verified=True,
        checkpoint_sha256=hashlib.sha256((source/'policy.zip').read_bytes()).hexdigest())))
    config = tmp_path/'environment.json'
    config.write_text('{}')
    output = tmp_path/'session'
    monkeypatch.setattr(sys, 'argv', ['parallel_session.py', '--config', str(config),
        '--source-run', str(source), '--output', str(output), '--chunk-steps', '128', '--total-steps', '256'])
    cuda = SimpleNamespace(is_available=lambda:True, get_device_name=lambda:'synthetic-GPU',
                           mem_get_info=lambda:(12*1024**3, 16*1024**3))
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(cuda=cuda))

    class Worker:
        count = 0

        def __init__(self, command, **kwargs):
            Worker.count += 1
            self.pid, self.returncode = Worker.count, 0
            root = Path(command[command.index('--output')+1])
            root.mkdir()
            (root/'report.json').write_text(json.dumps(dict(status='completed', steps=128,
                evaluation=dict(success_rate=.5, records=[dict(episode_return=-1.) for _ in range(8)]))))

        def poll(self):
            return self.returncode

    monkeypatch.setattr(session.subprocess, 'Popen', Worker)
    session.main()
    state = json.loads((output/'session.json').read_text())
    assert state['status'] == 'budget_complete' and state['consumed_steps'] == 256
    assert len(state['rounds']) == 1 and len(state['rounds'][0]['jobs']) == 2
    assert state['rounds'][0]['selection_success_rate'] == .5


def test_status_does_not_trust_a_dead_or_reused_pid():
    path = Path(__file__).resolve().parents[1]/'training/autonomous-manipulation/parallel_session_status.py'
    spec = importlib.util.spec_from_file_location('parallel_session_status', path)
    status = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(status)
    state = dict(status='running', process_create_time=50., heartbeat_unix_s=100.)
    assert status.effective_status(state, process_created_at=None, now_s=110.) == 'interrupted'
    assert status.effective_status(state, process_created_at=90., now_s=110.) == 'interrupted_pid_reused'
    assert status.effective_status(state, process_created_at=50., now_s=110.) == 'running'
    assert status.effective_status(state, process_created_at=50., now_s=230.) == 'stalled_or_suspended'
