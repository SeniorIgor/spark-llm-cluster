# Infrastructure

## Architecture

Spark standalone cluster:
- `ecetesla1`: master + worker
- `ecetesla2`: worker
- `ecetesla4`: worker
- one NVIDIA RTX 3070 8 GB per host

Ports: master `17377`, master UI `17380`, worker `17378`, worker UI `17381`, driver `17379`, application UI `17384`.

`/home/itiapkin` is shared between hosts. `/tmp/itiapkin/spark-llm` is host-local disposable runtime state.

## Bootstrap

If `/tmp/itiapkin/spark-llm` is missing, run on each host:

`bash /home/itiapkin/spark-llm-cluster/scripts/bootstrap_host.sh`

## Start

On `ecetesla1`:

`bash /home/itiapkin/spark-llm-cluster/scripts/start_master.sh`

Then on all three hosts:

`bash /home/itiapkin/spark-llm-cluster/scripts/start_worker.sh`

## Status

`bash /home/itiapkin/spark-llm-cluster/scripts/status_host.sh`

## Stop

On all three hosts:

`bash /home/itiapkin/spark-llm-cluster/scripts/stop_worker.sh`

Then on `ecetesla1`:

`bash /home/itiapkin/spark-llm-cluster/scripts/stop_master.sh`

## Distributed CUDA smoke test

Run on `ecetesla1`:

`bash /home/itiapkin/spark-llm-cluster/scripts/run_smoke_test.sh`

Success ends with `ALL_3_WORKERS_CUDA_OK`.

## Spark Master UI

From the Mac:

`ssh -N -i ~/.ssh/uwaterloo_gitlab -o IdentitiesOnly=yes -L 17380:localhost:17380 itiapkin@ecetesla1.uwaterloo.ca`

Then open `http://localhost:17380`.

## Validated checkpoint

Validated on 2026-09-25:
- all three workers registered with the Spark master;
- each worker advertised one RTX 3070;
- the cluster was stopped and recreated using this repository;
- the distributed Spark -> PyTorch -> CUDA smoke test passed on all three hosts.
