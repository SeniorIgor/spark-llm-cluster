# Feasibility Pilot

This directory preserves the reproducible artifacts from the ECE 750 SPARK-LLM feasibility pilot run on the Waterloo `ecetesla1`, `ecetesla2`, and `ecetesla4` machines.

## Configuration

- Model: `Qwen/Qwen2.5-1.5B-Instruct`
- Model revision: `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- Dataset: `launch/gov_report`
- Dataset revision: `32feeaede49fed993aef070bc4da09263fd0429a`
- Source chunk size: 2,048 tokens
- GPUs: 3 × NVIDIA RTX 3070 8 GiB

The disposable runtime environment was created under:

`/tmp/itiapkin/spark-llm`

That directory contained the Python virtual environment, Hugging Face model cache, Spark runtime files, and other temporary state. It is intentionally not stored in Git.

## Scripts

- `spark_qwen_smoke.py` — validates Spark → Qwen → CUDA execution on the three GPU workers.
- `govreport_token_audit.py` — reconstructs the pinned GovReport training corpus and measures source-token lengths with the pinned Qwen tokenizer.
- `govreport_workload_feasibility.py` — constructs the low, moderate, and high document-length-variability feasibility workloads.

The reusable Spark cluster bootstrap and CUDA validation scripts remain in the repository-level `scripts/` directory.

## Evidence

The `evidence/` directory contains:

- machine and CUDA inventories for all three ECE hosts;
- Python package snapshots;
- GovReport token-length statistics for all 17,519 training documents;
- per-document token lengths;
- feasibility workload statistics;
- the three 300-document workload manifests.

Large runtime artifacts such as model weights, Hugging Face caches, virtual environments, raw downloaded dataset files, and Spark logs are not committed.
