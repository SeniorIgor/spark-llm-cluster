import socket
from pyspark import SparkContext, TaskContext

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
CACHE = "/tmp/itiapkin/spark-llm/hf-cache"

def run_partition(rows):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    ctx = TaskContext.get()
    gpu_addresses = ctx.resources()["gpu"].addresses

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL,
        revision=REVISION,
        cache_dir=CACHE,
        local_files_only=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        revision=REVISION,
        cache_dir=CACHE,
        local_files_only=True,
        torch_dtype=torch.float16,
    ).eval().to("cuda")

    messages = [{
        "role": "user",
        "content": "In one sentence, explain why load imbalance can slow a distributed system."
    }]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    torch.cuda.reset_peak_memory_stats()

    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,
            use_cache=True,
        )

    generated = output[0, inputs.input_ids.shape[1]:]

    yield {
        "host": socket.gethostname(),
        "spark_gpu": list(gpu_addresses),
        "cuda_device": torch.cuda.get_device_name(0),
        "peak_reserved_gib": round(
            torch.cuda.max_memory_reserved() / 1024**3, 3
        ),
        "output": tokenizer.decode(
            generated,
            skip_special_tokens=True,
        ),
    }

sc = SparkContext.getOrCreate()

results = (
    sc.parallelize([1, 2, 3], 3)
      .mapPartitions(run_partition)
      .collect()
)

print("=== SPARK QWEN RESULTS ===")
for result in sorted(results, key=lambda x: x["host"]):
    print(result)

hosts = {r["host"] for r in results}

print("unique_hosts:", sorted(hosts))
print("worker_count:", len(hosts))

if len(hosts) != 3:
    raise RuntimeError(f"Expected 3 workers, got {len(hosts)}")

print("SPARK_QWEN_3_WORKERS_OK")

sc.stop()
