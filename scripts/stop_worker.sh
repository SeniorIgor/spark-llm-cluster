#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"

PIDFILE="$CLUSTER_LOCAL/worker.pid"

if [[ ! -f "$PIDFILE" ]] || ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Spark worker is not running"
  rm -f "$PIDFILE"
  exit 0
fi

pid="$(cat "$PIDFILE")"
kill "$pid"

for _ in {1..20}; do
  kill -0 "$pid" 2>/dev/null || break
  sleep 0.25
done

rm -f "$PIDFILE"
echo "Spark worker stopped"
