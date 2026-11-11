"""Check actual session liveness; a persisted running label is not sufficient."""
import argparse
import json
from pathlib import Path
import time


def effective_status(state, *, process_created_at, now_s):
    if state['status'] != 'running':
        return state['status']
    if process_created_at is None:
        return 'interrupted'
    expected = state.get('process_create_time')
    if expected is not None and abs(expected-process_created_at) > .01:
        return 'interrupted_pid_reused'
    heartbeat = state.get('heartbeat_unix_s')
    if heartbeat is None:
        return 'unverified_legacy_status'
    if now_s < heartbeat or now_s-heartbeat > 120:
        return 'stalled_or_suspended'
    return 'running'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True, help='Session folder containing session.json')
    args = parser.parse_args()
    import psutil
    state = json.loads((args.session/'session.json').read_text(encoding='utf-8'))
    created = None
    try:
        process = psutil.Process(state['pid'])
        if process.is_running():
            created = process.create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    print(json.dumps(dict(saved_status=state['status'], effective_status=effective_status(
        state, process_created_at=created, now_s=time.time()), pid=state['pid'],
        heartbeat_unix_s=state.get('heartbeat_unix_s'),
        latest_round=state.get('rounds', [])[-1:] or None), indent=2))


if __name__ == '__main__':
    main()
