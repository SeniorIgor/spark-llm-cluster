#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "$0")/common.sh"

python3 -c 'import sys,platform; assert sys.version_info[:2] == (3,12); assert platform.machine() == "x86_64"'

java -version 2>&1 | grep -E 'version "21[.]' >/dev/null || {
  echo "Java 21 required" >&2
  exit 1
}

python3 -m venv "$CLUSTER_LOCAL/venv"

"$CLUSTER_PY" -m pip install --disable-pip-version-check pip==25.0.1
"$CLUSTER_PY" -m pip install --disable-pip-version-check \
  -r "$CLUSTER_REPO/requirements/cluster.txt"

"$CLUSTER_PY" -m pip check

"$CLUSTER_PY" -c '
import torch, pyspark
assert torch.__version__ == "2.6.0+cu124"
assert pyspark.__version__ == "4.0.1"
print("torch:", torch.__version__)
print("pyspark:", pyspark.__version__)
'

"$CLUSTER_PY" -m pip freeze \
  > "$CLUSTER_REPO/docs/evidence/$CLUSTER_HOST-freeze.txt"

"$CLUSTER_PY" "$CLUSTER_REPO/scripts/verify_cuda.py" \
  --output "$CLUSTER_REPO/docs/evidence/$CLUSTER_HOST-cuda.json"
