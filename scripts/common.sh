#!/usr/bin/env bash
set -euo pipefail
umask 077

CLUSTER_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER_HOST="$(hostname -s)"

case "$CLUSTER_HOST" in
  ecetesla1|ecetesla2|ecetesla4) ;;
  *)
    echo "Unexpected host: $CLUSTER_HOST" >&2
    exit 1
    ;;
esac

[[ "$(id -un)" == "itiapkin" ]] || {
  echo "Expected user itiapkin" >&2
  exit 1
}

CLUSTER_LOCAL=/tmp/itiapkin/spark-llm

for dir in /tmp/itiapkin "$CLUSTER_LOCAL"; do
  [[ ! -L "$dir" ]] || {
    echo "Refusing symlink: $dir" >&2
    exit 1
  }

  if [[ -e "$dir" ]]; then
    [[ -d "$dir" && -O "$dir" ]] || {
      echo "Not an owned directory: $dir" >&2
      exit 1
    }
  else
    mkdir -m 700 "$dir"
  fi
done

CLUSTER_PY="$CLUSTER_LOCAL/venv/bin/python"

export PIP_CACHE_DIR="$CLUSTER_LOCAL/cache"
export TMPDIR="$CLUSTER_LOCAL/tmp"
export PYSPARK_PYTHON="$CLUSTER_PY"
export PYSPARK_DRIVER_PYTHON="$CLUSTER_PY"

mkdir -p \
  "$TMPDIR" \
  "$CLUSTER_LOCAL/logs" \
  "$CLUSTER_REPO/docs/evidence"
