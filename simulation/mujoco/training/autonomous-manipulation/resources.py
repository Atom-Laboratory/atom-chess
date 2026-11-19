"""Measured process and GPU telemetry, sampled outside policy inputs."""
import os
import subprocess
import time

import torch


def sample_hardware(device):
    sample = dict(unix_s=time.time(), pid=os.getpid(), device=device,
                  cpu_process_s=sum(os.times()[:2]), cpu_percent=None, ram_process_bytes=None)
    try:
        import psutil
        process = psutil.Process()
        sample.update(cpu_percent=psutil.cpu_percent(), ram_process_bytes=process.memory_info().rss,
                      ram_system_percent=psutil.virtual_memory().percent)
    except ImportError:
        sample['cpu_ram_monitor'] = 'psutil unavailable'
    if device == 'cuda':
        sample.update(gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda,
                      torch_allocated_bytes=torch.cuda.memory_allocated(),
                      torch_reserved_bytes=torch.cuda.memory_reserved())
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,temperature.gpu',
                '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True, timeout=3)
            values = result.stdout.splitlines()[0].split(',')
            sample.update(gpu_utilization_percent=float(values[0]), gpu_memory_mib=float(values[1]),
                          gpu_temperature_c=float(values[2]))
        except (OSError, subprocess.SubprocessError, ValueError, IndexError) as error:
            sample['nvidia_smi_error'] = repr(error)
    return sample
