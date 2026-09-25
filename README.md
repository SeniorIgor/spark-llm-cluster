# spark-llm-cluster

Reproducible bootstrap and lifecycle tooling for the three-node GPU Spark cluster used by SPARK-LLM.

## Cluster

| Host | Role | GPU |
|---|---|---|
| ecetesla1 | Spark master + worker | NVIDIA RTX 3070 8 GB |
| ecetesla2 | Spark worker | NVIDIA RTX 3070 8 GB |
| ecetesla4 | Spark worker | NVIDIA RTX 3070 8 GB |

Software baseline:

- Python 3.12
- Java 21
- Spark / PySpark 4.0.1
- PyTorch 2.6.0+cu124

Runtime state is stored under `/tmp/itiapkin/spark-llm` and is disposable.

The Git repository contains the persistent configuration and scripts required to recreate the cluster.

See `docs/infrastructure.md` for operational instructions.
