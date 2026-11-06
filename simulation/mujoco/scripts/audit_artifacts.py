"""Inventory MuJoCo artifacts and propose migration without moving source data."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, OSError):
        return {}


def classify(path, records):
    run = records.get('run.json', {})
    report = records.get('report.json', {})
    manifest = records.get('manifest.json', {})
    if isinstance(run, dict) and 'environment' in run:
        env = run['environment']
        if isinstance(env, dict) and 'configuration' in env:
            return 'training/camera-manipulation/runs', 'P038 environment configuration in run.json'
        if isinstance(env, dict):
            return 'training/grasp-lift/runs', 'Legacy environment metadata in run.json'
    if isinstance(manifest, dict) and 'model_sha256' in manifest:
        if manifest.get('fixture_kind') == 'two_piece_capture':
            return 'examples/prepare_capture_task/runs', 'Two-piece capture fixture manifest'
        return 'assets/bundles', 'Has hashed model manifest; shared consumers require path review'
    if isinstance(report, dict):
        if report.get('evidence_source') == 'rgb_only' or 'graveyard_slot' in report:
            return 'examples/prepare_capture_task/runs', 'Capture evidence report'
        if 'polygon_px' in report and 'slot' in report:
            return 'examples/prepare_capture_task/runs', 'Graveyard camera qualification report'
        if 'layout_sha256' in report and 'results' in report:
            return 'examples/validate_board_reference/runs', 'Marker-layout qualification report'
        if 'actor_features' in report:
            return 'examples/preview_native_policy/runs', 'Actor-input preview report'
        if 'camera_status' in report:
            return 'examples/validate_native_perception/runs', 'Native perception report'
    return None, 'Origin unresolved; preserve in place pending content/dependency review'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    repo = module.parents[1]
    source = module/'runs'
    args.output.mkdir(parents=True, exist_ok=False)
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=repo, text=True).splitlines()
    references = []
    for name in tracked:
        p = repo/name
        if p.suffix.lower() not in ('.py', '.ps1', '.md', '.json', '.yaml', '.yml', '.toml', '.txt'):
            continue
        try:
            for number, line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(), 1):
                if 'runs/' in line or 'runs\\' in line or "'runs'" in line or '"runs"' in line:
                    references.append(dict(file=name, line=number, text=line))
        except (OSError, UnicodeError):
            continue
    items, checkpoints = [], []
    for entry in sorted(source.iterdir()):
        files = sorted(p for p in entry.rglob('*') if p.is_file()) if entry.is_dir() else [entry]
        records = {}
        inventory = []
        dependencies = []
        for p in files:
            relative = p.relative_to(entry).as_posix() if entry.is_dir() else p.name
            inventory.append(dict(path=relative, bytes=p.stat().st_size, sha256=digest(p)))
            if p.suffix == '.json':
                data = read_json(p)
                records[relative] = data
                if isinstance(data, dict):
                    encoded = json.dumps(data)
                    if 'runs/' in encoded or 'runs\\' in encoded or ':\\' in encoded:
                        dependencies.append(relative)
            if p.suffix == '.xml':
                text = p.read_text(encoding='utf-8', errors='replace')
                if ':/' in text or ':\\' in text or 'runs/' in text:
                    dependencies.append(relative)
            if p.suffix == '.zip':
                record = dict(path=p.relative_to(repo).as_posix(), sha256=inventory[-1]['sha256'])
                try:
                    with zipfile.ZipFile(p) as archive:
                        members = archive.namelist()
                        record['members'] = members
                        record['optimizer_present'] = 'policy.optimizer.pth' in members
                        if 'data' in members:
                            data = json.loads(archive.read('data'))
                            record['policy_metadata'] = {k: data.get(k) for k in
                                ('num_timesteps', 'seed', 'n_steps', 'batch_size', 'n_epochs', 'learning_rate')}
                            record['spaces'] = {k: {a:b for a,b in data.get(k, {}).items()
                                if a != ':serialized:'} for k in ('action_space', 'observation_space')
                                if isinstance(data.get(k), dict)}
                    record['resume_status'] = 'pending full environment/provenance validation'
                except (OSError, ValueError, zipfile.BadZipFile) as error:
                    record['error'] = str(error)
                checkpoints.append(record)
        destination, reason = classify(entry, records)
        matches = [r for r in references if entry.name in r['text']]
        item = dict(original=entry.relative_to(repo).as_posix(),
                    proposed=(module/ destination/entry.name).relative_to(repo).as_posix() if destination else None,
                    reason=reason, state='referenced; activity unverified' if matches else 'historical or unclassified; activity unverified',
                    file_types=dict(Counter(p.suffix or '(none)' for p in files)),
                    files=inventory, path_dependencies=dependencies, source_references=matches)
        # Preserve nested multi-stage runs as a unit until their lineage is resolved.
        item['nested_records'] = sorted(records)
        items.append(item)
    report = dict(schema=1, status='proposal_only_no_data_moved', entries=items,
                  checkpoints=checkpoints, source_references=references)
    (args.output/'inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    lines = ['# MuJoCo migration proposal', '',
             'This inventory is a proposal. Source artifacts remain in their original locations.',
             'Every source file has a recorded SHA-256 and size in inventory.json.',
             'Activity is not inferred from directory names. Unresolved entries remain in place.',
             '', '| Original | Proposed destination | Evidence | Dependencies |',
             '|---|---|---|---|']
    for item in items:
        lines.append('| '+item['original']+' | '+(item['proposed'] or 'Preserve pending classification')+' | '+
                     item['reason']+' | '+str(len(item['path_dependencies']))+' artifact references; '+
                     str(len(item['source_references']))+' source references |')
    lines += ['', '## Checkpoints', '',
              'Optimizer presence alone does not prove resumability. Original environment,',
              'configuration, libraries, source signatures and policy spaces must agree.',
              'The current wrist profile adds a commanded joint while P038 still declares',
              'four policy actions and five commanded joints. No recorded policy is qualified',
              'for wrist control by this inventory.', '',
              '| Checkpoint | Optimizer present | Resume status |','|---|---|---|']
    for c in checkpoints:
        lines.append('| '+c['path']+' | '+str(c.get('optimizer_present',False))+' | '+c.get('resume_status',c.get('error','unknown'))+' |')
    (args.output/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(entries=len(items), files=sum(len(i['files']) for i in items),
                         checkpoints=len(checkpoints), references=len(references),
                         unresolved=sum(i['proposed'] is None for i in items))))


if __name__ == '__main__':
    main()
