"""Bounded native CUDA kernel and MuJoCo Warp contact smoke qualification."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback
import uuid

import numpy as np
import psutil


CONTACT_XML = '''<mujoco model="atom_gpu_contact_smoke">
  <option timestep=".002" gravity="0 0 -9.81" integrator="implicitfast" cone="elliptic" impratio="10"/>
  <worldbody><geom name="floor" type="plane" size="1 1 .1" friction="1.2 .01 .001"/>
    <body name="pawn_mass_probe" pos="0 0 .08"><freejoint/>
      <geom name="ball" type="sphere" size=".01" mass=".02" friction="1.2 .01 .001" condim="4"/>
    </body>
  </worldbody></mujoco>'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gpu_status():
    result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,compute_cap,memory.total,memory.free,utilization.gpu',
                             '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10, check=True)
    fields = result.stdout.strip().splitlines()[0].split(', ')
    return dict(zip(('name','driver','compute_capability','total_mib','free_mib','utilization_percent'), fields))


def validate_args(args):
    if (not 1 <= args.worlds <= 1024 or not 1 <= args.steps <= 10000
            or not np.isfinite(args.max_wall_s) or not 1 <= args.max_wall_s <= 1800
            or not 128 <= args.max_gpu_mib <= 8192):
        raise ValueError('Worlds 1..1024, steps 1..10000, wall 1..1800 s, GPU budget 128..8192 MiB required')


def worker(args):
    import mujoco
    import mujoco_warp as mjw
    import warp as wp
    from kernels import square
    started = time.perf_counter()
    hardware_before = gpu_status()
    if float(hardware_before['free_mib']) < args.max_gpu_mib+1024:
        raise MemoryError('Requested GPU budget plus 1 GiB headroom unavailable; use a smaller budget')
    wp.init()
    device = wp.get_device('cuda:0')
    values = np.arange(1024, dtype=np.float32)
    with wp.ScopedDevice(device):
        gpu_values = wp.array(values, dtype=wp.float32)
        result = wp.empty(1024, dtype=wp.float32)
        kernel_started = time.perf_counter()
        wp.launch(square, dim=1024, inputs=[gpu_values, result])
        wp.synchronize_device(device)
        kernel_wall = time.perf_counter()-kernel_started
        np.testing.assert_array_equal(result.numpy(), values*values)

        model = mujoco.MjModel.from_xml_string(CONTACT_XML)
        cpu = mujoco.MjData(model)
        mujoco.mj_forward(model, cpu)
        gpu_model = mjw.put_model(model)
        data = mjw.put_data(model, cpu, nworld=args.worlds, nconmax=64, njmax=256)
        allocation = wp.get_mempool_used_mem_current(device)
        if allocation > args.max_gpu_mib*1024**2:
            raise MemoryError(f'Warp memory pool {allocation} exceeds declared budget')
        compile_started = time.perf_counter()
        mjw.step(gpu_model, data)
        wp.synchronize_device(device)
        first_step_wall = time.perf_counter()-compile_started
        signature = int(mujoco.mjtState.mjSTATE_INTEGRATION)
        state = np.empty(mujoco.mj_stateSize(model, signature))
        mujoco.mj_getState(model, cpu, state, signature)
        states = wp.array(np.tile(state, (args.worlds, 1)).astype(np.float32), dtype=wp.float32)
        mjw.set_state(gpu_model, data, states, signature)
        with wp.ScopedCapture(device=device) as capture:
            mjw.step(gpu_model, data)
        wp.synchronize_device(device)
        physics_started = time.perf_counter()
        for _ in range(args.steps):
            wp.capture_launch(capture.graph)
        wp.synchronize_device(device)
        physics_wall = time.perf_counter()-physics_started
        overflow = data.overflow.numpy()
        if np.any(overflow):
            raise RuntimeError(f'MJWarp overflow/iteration flags: {overflow.tolist()}')
        positions, velocities = data.qpos.numpy(), data.qvel.numpy()
        if not np.isfinite(positions).all() or not np.isfinite(velocities).all():
            raise RuntimeError('Nonfinite GPU physics state')
        cpu_started = time.perf_counter()
        for _ in range(args.steps):
            mujoco.mj_step(model, cpu)
        cpu_wall = time.perf_counter()-cpu_started
        error = float(np.max(abs(positions-cpu.qpos)))
        if error > 1e-4:
            raise RuntimeError(f'Primitive contact final position differs by {error} (>1e-4)')
        allocation_high = wp.get_mempool_used_mem_high(device)
        if allocation_high > args.max_gpu_mib*1024**2:
            raise MemoryError('Peak Warp pool exceeds declared budget')
        nacon = int(data.nacon.numpy()[0])
        nefc_max = int(data.nefc.numpy().max())
        if nacon > data.naconmax or nefc_max > data.njmax:
            raise RuntimeError('Contact/constraint capacity exceeded')
    report = dict(schema=1, status='GPU_CONTACT_SMOKE_PASSED', experiment='EXP-0002',
        scope='primitive contact and CUDA execution only; not robot parity or training throughput',
        versions={name:importlib.metadata.version(name) for name in ('mujoco','mujoco-warp','warp-lang','numpy')},
        hardware_before=hardware_before, hardware_after=gpu_status(),
        device=dict(name=device.name,arch=device.arch), os=platform.platform(), python=sys.version,
        cpu_logical=psutil.cpu_count(), ram_total_bytes=psutil.virtual_memory().total,
        worlds=args.worlds, steps=args.steps, budgets=dict(max_wall_s=args.max_wall_s,max_gpu_mib=args.max_gpu_mib),
        cuda_kernel_wall_s=kernel_wall, first_gpu_step_compile_wall_s=first_step_wall,
        gpu_physics_wall_s=physics_wall, cpu_single_world_wall_s=cpu_wall,
        aggregate_gpu_physics_steps_per_s=args.steps*args.worlds/physics_wall,
        final_qpos_max_abs_error_m=error, final_gpu_qpos=positions.tolist(),
        capacities=dict(naconmax=data.naconmax,njmax=data.njmax), final_nacon=nacon,
        final_nefc_max=nefc_max, overflow=overflow.tolist(), warp_pool_high_bytes=allocation_high,
        execution_wall_s=time.perf_counter()-started,
        source_sha256={p.name:sha(p) for p in (Path(__file__),Path(__file__).with_name('kernels.py'))},
        lock_sha256=sha(Path(__file__).with_name('requirements-windows-py312.lock')))
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worlds', type=int, default=1)
    parser.add_argument('--steps', type=int, default=500)
    parser.add_argument('--max-wall-s', type=float, default=180.)
    parser.add_argument('--max-gpu-mib', type=int, default=2048)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try: validate_args(args)
    except ValueError as error: parser.error(str(error))
    if args.worker:
        try: worker(args)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error),
                traceback=traceback.format_exc()),indent=2),encoding='utf-8')
            raise
        return
    output = (args.output or Path(__file__).parent/'runs/EXP-0002'/('RUN-'+uuid.uuid4().hex)).resolve()
    output.mkdir(parents=True,exist_ok=False)
    snapshot = output/'source'
    snapshot.mkdir()
    for name in ('probe.py','kernels.py','requirements-windows-py312.lock'):
        shutil.copyfile(Path(__file__).with_name(name), snapshot/name)
    revision = subprocess.run(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[3],
                              capture_output=True,text=True,timeout=10,check=True).stdout.strip()
    (output/'request.json').write_text(json.dumps(dict(worlds=args.worlds,steps=args.steps,
        max_wall_s=args.max_wall_s,max_gpu_mib=args.max_gpu_mib,source_commit=revision,
        source_sha256={p.name:sha(p) for p in snapshot.iterdir()}),indent=2),encoding='utf-8')
    command = [sys.executable,'-u','-B',str(snapshot/'probe.py'),'--worker','--output',str(output),
        '--worlds',str(args.worlds),'--steps',str(args.steps),'--max-wall-s',str(args.max_wall_s),
        '--max-gpu-mib',str(args.max_gpu_mib)]
    print(f'[ATOM GPU] bounded CUDA/contact smoke | {args.worlds} worlds | {output}',flush=True)
    process_started = time.perf_counter()
    try:
        with (output/'stdout.log').open('x',encoding='utf-8') as stdout, (output/'stderr.log').open('x',encoding='utf-8') as stderr:
            subprocess.run(command,cwd=output,stdout=stdout,stderr=stderr,timeout=args.max_wall_s,check=True)
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
        if not (output/'failure.json').exists():
            (output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error)),indent=2))
        print(f'[ATOM GPU] FAILED | inspect {output}',flush=True)
        raise
    report=json.loads((output/'report.json').read_text())
    report['process_wall_s'] = time.perf_counter()-process_started
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('status','device','worlds','steps','final_qpos_max_abs_error_m')}),flush=True)


if __name__ == '__main__':
    main()
