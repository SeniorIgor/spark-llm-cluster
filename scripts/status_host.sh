#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"

show_process() {
  local name="$1"
  local pidfile="$2"

  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "$name: RUNNING (PID $(cat "$pidfile"))"
  else
    echo "$name: STOPPED"
  fi
}

echo "Host: $CLUSTER_HOST"

if [[ "$CLUSTER_HOST" == "ecetesla1" ]]; then
  show_process "Master" "$CLUSTER_LOCAL/master.pid"
fi

show_process "Worker" "$CLUSTER_LOCAL/worker.pid"

nvidia-smi \
  --query-gpu=name,uuid,memory.used,memory.total,utilization.gpu \
  --format=csv,noheader
