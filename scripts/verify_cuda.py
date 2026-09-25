#!/usr/bin/env python3
"""Real CUDA computation, shared by direct and distributed tests."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def cuda_work(seconds=0):
    import torch
    assert torch.__version__ == '2.6.0+cu124', torch.__version__
    assert torch.cuda.is_available(), 'CUDA unavailable; CPU fallback forbidden'
    assert torch.cuda.device_count() == 1, 'Expected exactly one visible assigned GPU'
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()
    started = time.time()
    start = time.monotonic()
    # Exactly representable FP32 result. Validate the entire output on the GPU.
    a = torch.ones((1024, 1024), device='cuda')
    b = torch.full((1024, 1024), 2.0, device='cuda')
    iterations = 0
    while True:
        c = a @ b
        torch.cuda.synchronize()
        iterations += 1
        if time.monotonic() - start >= seconds:
            break
    assert c.is_cuda and bool(torch.all(c == 2048).item()), 'Incorrect CUDA matmul'
    smi = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,memory.used,utilization.gpu,driver_version', '--format=csv,noheader'], text=True).strip()
    return {'hostname': socket.gethostname().split('.')[0], 'pid': os.getpid(),
            'timestamp': datetime.now(timezone.utc).isoformat(), 'started_epoch': started,
            'ended_epoch': time.time(), 'duration_s': time.monotonic() - start,
            'cuda_available': True, 'torch': torch.__version__, 'cuda_runtime': torch.version.cuda,
            'gpu': torch.cuda.get_device_name(0), 'torch_device': 0,
            'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES'),
            'result': c[0, 0].item(), 'iterations': iterations,
            'peak_memory_bytes': torch.cuda.max_memory_allocated(), 'nvidia_smi': smi,
            'success': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = cuda_work()
    result['boot_id'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    result['python_executable'] = os.sys.executable
    data = json.dumps(result, indent=2)
    print(data)
    if args.output:
        args.output.write_text(data + '\n')
