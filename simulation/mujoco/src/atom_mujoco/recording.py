"""Small local JSON records, with provenance and exclusive output creation."""
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import platform
import subprocess

import json
import numpy as np


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    return value


def provenance():
    location = Path(__file__).resolve().parent
    try:
        def git(*args):
            return subprocess.check_output(['git', '-C', str(location), *args],
                                           stderr=subprocess.DEVNULL, timeout=10).decode().strip()
        revision = git('rev-parse', 'HEAD')
        tracked_dirty = bool(git('status', '--porcelain', '--untracked-files=no'))
        untracked = bool(git('ls-files', '--others', '--exclude-standard', '--', ':/'))
    except (OSError, subprocess.SubprocessError):
        revision, tracked_dirty, untracked = None, None, None
    return {'utc': datetime.now(timezone.utc).isoformat(), 'git_commit': revision,
            'tracked_dirty': tracked_dirty, 'untracked_present': untracked,
            'python': platform.python_version(), 'platform': platform.platform(),
            'packages': {name: version(name) for name in ('atom-mujoco', 'mujoco', 'numpy')}}


def save_record(path, result):
    """Serialize fully before opening: invalid values cannot truncate old results."""
    payload = json.dumps(json_value(result), indent=2, allow_nan=False)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)
