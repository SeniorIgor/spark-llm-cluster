#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"

SPARK_HOME="$CLUSTER_LOCAL/venv/lib/python3.12/site-packages/pyspark"
PIDFILE="$CLUSTER_LOCAL/worker.pid"
LOG="$CLUSTER_LOCAL/logs/worker.log"

[[ -x "$SPARK_HOME/bin/spark-class" ]] || {
  echo "Spark is not bootstrapped. Run bootstrap_host.sh first." >&2
  exit 1
}

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Spark worker already running (PID $(cat "$PIDFILE"))"
  exit 0
fi

mkdir -p "$CLUSTER_LOCAL/worker"

nohup "$SPARK_HOME/bin/spark-class" \
  org.apache.spark.deploy.worker.Worker \
  --host "$CLUSTER_HOST.uwaterloo.ca" \
  --port 17378 \
  --webui-port 17381 \
  --cores 4 \
  --memory 8G \
  --work-dir "$CLUSTER_LOCAL/worker" \
  --properties-file "$CLUSTER_REPO/config/worker.properties" \
  spark://ecetesla1.uwaterloo.ca:17377 \
  > "$LOG" 2>&1 < /dev/null &

echo $! > "$PIDFILE"
sleep 3

kill -0 "$(cat "$PIDFILE")"
echo "Spark worker started (PID $(cat "$PIDFILE"))"
grep -E 'gpu ->|Successfully registered' "$LOG" | tail -2 || true
