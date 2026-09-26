#!/usr/bin/env python3
"""Read-only inventory; temporary socket binds close immediately."""
import importlib.util
import json
import os
import platform
import pwd
import shutil
import socket
import subprocess
from datetime import datetime, timezone

HOSTS = ['ecetesla1', 'ecetesla2', 'ecetesla4']
PORTS = list(range(17377, 17385))

def command(args):
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=15)
        return {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'error': str(e)}

def main():
    result = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'hostname': socket.gethostname(), 'os': platform.freedesktop_os_release(),
              'python': platform.python_version(), 'architecture': platform.machine(),
              'shell': pwd.getpwuid(os.getuid()).pw_shell,
              'java': command(['java', '-version']),
              'nvidia_smi': command(['nvidia-smi']),
              'gpu': command(['nvidia-smi', '--query-gpu=index,uuid,name,memory.total,driver_version', '--format=csv,noheader']),
              'storage': command(['df', '-hT', '/tmp', '/home/itiapkin']),
              'spark_submit': shutil.which('spark-submit'),
              'packages': {p: importlib.util.find_spec(p) is not None for p in ['torch', 'pyspark']},
              'ports_bindable': {}, 'peers': {}}
    for port in PORTS:
        with socket.socket() as s:
            try:
                s.bind(('0.0.0.0', port))
                result['ports_bindable'][port] = True
            except OSError as e:
                result['ports_bindable'][port] = str(e)
    for host in HOSTS:
        fqdn = host + '.uwaterloo.ca'
        try:
            ips = sorted({x[4][0] for x in socket.getaddrinfo(fqdn, 22, type=socket.SOCK_STREAM)})
            with socket.create_connection((fqdn, 22), timeout=3):
                pass
            result['peers'][host] = {'ips': ips, 'tcp22': True}
        except OSError as e:
            result['peers'][host] = {'error': str(e)}
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
