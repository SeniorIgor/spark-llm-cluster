#!/usr/bin/env python3
import json
import subprocess

rows = subprocess.check_output(
    ["nvidia-smi", "--query-gpu=uuid,name", "--format=csv,noheader"],
    text=True,
).strip().splitlines()

if len(rows) != 1:
    raise RuntimeError(f"Expected exactly one GPU, got: {rows}")

uuid, name = [x.strip() for x in rows[0].split(",", 1)]

if "RTX 3070" not in name:
    raise RuntimeError(f"Expected RTX 3070, got: {name}")

print(json.dumps({
    "name": "gpu",
    "addresses": [uuid],
}))
