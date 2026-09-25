#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "$0")/common.sh"

[[ "$CLUSTER_HOST" == "ecetesla1" ]] || {
  echo "Run this script on ecetesla1" >&2
  exit 1
}

SPARK_HOME="$CLUSTER_LOCAL/venv/lib/python3.12/site-packages/pyspark"

"$SPARK_HOME/bin/spark-submit" \
  --master spark://ecetesla1.uwaterloo.ca:17377 \
  --total-executor-cores 3 \
  --conf spark.executor.cores=1 \
  --conf spark.executor.resource.gpu.amount=1 \
  --conf spark.task.resource.gpu.amount=1 \
  --conf spark.pyspark.python="$CLUSTER_PY" \
  --conf spark.driver.host=ecetesla1.uwaterloo.ca \
  --conf spark.driver.port=17379 \
  --conf spark.ui.port=17384 \
  "$CLUSTER_REPO/scripts/spark_cuda_smoke.py"
