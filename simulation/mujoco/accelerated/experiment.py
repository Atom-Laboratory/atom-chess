"""Fresh, immutable-source, time-bounded subprocess experiments."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid


def bounded_run(script, arguments, *, experiment, output=None, sources=(), max_wall_s=180., request=None):
    script=Path(script).resolve()
    if not 1 <= max_wall_s <= 1800:raise ValueError('Finite process budget in [1, 1800] seconds required')
    output=Path(output or script.parent/'runs'/experiment/('RUN-'+uuid.uuid4().hex)).resolve()
    output.mkdir(parents=True,exist_ok=False)
    snapshot=output/'source';snapshot.mkdir()
    for source in (script,Path(__file__),*map(Path,sources)):
        destination=snapshot/source.name
        if not destination.exists():shutil.copyfile(source,destination)
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=script.parents[3],capture_output=True,
                            text=True,timeout=10,check=True).stdout.strip()
    metadata=dict(request or {},experiment=experiment,source_commit=revision,
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()})
    (output/'request.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    command=[sys.executable,'-u','-B',str(snapshot/script.name),'--worker','--output',str(output),*arguments]
    print(f'[ATOM {experiment}] bounded run | {output}',flush=True)
    started=time.perf_counter()
    try:
        with (output/'stdout.log').open('x',encoding='utf-8') as stdout,(output/'stderr.log').open('x',encoding='utf-8') as stderr:
            subprocess.run(command,cwd=output,stdout=stdout,stderr=stderr,timeout=max_wall_s,check=True)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
        if not (output/'failure.json').exists():
            (output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error)),indent=2),encoding='utf-8')
        print(f'[ATOM {experiment}] FAILED | inspect {output}',flush=True)
        raise
    report=json.loads((output/'report.json').read_text(encoding='utf-8'))
    report.update(process_wall_s=time.perf_counter()-started,request_sha256=hashlib.sha256((output/'request.json').read_bytes()).hexdigest())
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return output,report
