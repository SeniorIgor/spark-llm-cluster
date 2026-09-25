import json
import os
import socket

from pyspark import SparkContext, TaskContext

sc = SparkContext.getOrCreate()

def test_gpu(_):
    import torch

    ctx = TaskContext.get()
    gpu = ctx.resources().get("gpu")
    assigned = gpu.addresses if gpu else []

    assert assigned, "Spark did not assign a GPU"
    assert torch.cuda.is_available(), "CUDA unavailable"

    torch.cuda.set_device(0)
    a = torch.ones((1024, 1024), device="cuda")
    b = torch.full((1024, 1024), 2.0, device="cuda")
    result = float((a @ b)[0, 0].item())

    assert result == 2048.0

    yield {
        "host": socket.gethostname(),
        "spark_gpu": assigned,
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "torch_gpu": torch.cuda.get_device_name(0),
        "result": result,
        "success": True,
    }

results = sc.parallelize(range(3), 3).mapPartitions(test_gpu).collect()

print("=== SPARK CUDA RESULTS ===")
for row in sorted(results, key=lambda x: x["host"]):
    print(json.dumps(row))

hosts = {x["host"] for x in results}
assert hosts == {"ecetesla1", "ecetesla2", "ecetesla4"}, f"Expected all 3 hosts, got {hosts}"

print("ALL_3_WORKERS_CUDA_OK")
sc.stop()
