#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"

[[ "$CLUSTER_HOST" == "ecetesla1" ]] || {
  echo "Master must run on ecetesla1" >&2
  exit 1
}

SPARK_HOME="$CLUSTER_LOCAL/venv/lib/python3.12/site-packages/pyspark"
PIDFILE="$CLUSTER_LOCAL/master.pid"
LOG="$CLUSTER_LOCAL/logs/master.log"

[[ -x "$SPARK_HOME/bin/spark-class" ]] || {
  echo "Spark is not bootstrapped. Run bootstrap_host.sh first." >&2
  exit 1
}

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Spark master already running (PID $(cat "$PIDFILE"))"
  exit 0
fi

nohup "$SPARK_HOME/bin/spark-class" \
  org.apache.spark.deploy.master.Master \
  --host ecetesla1.uwaterloo.ca \
  --port 17377 \
  --webui-port 17380 \
  > "$LOG" 2>&1 < /dev/null &

echo $! > "$PIDFILE"
sleep 2

kill -0 "$(cat "$PIDFILE")"
echo "Spark master started (PID $(cat "$PIDFILE"))"
