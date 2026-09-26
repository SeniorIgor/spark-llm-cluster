import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

DATASET = "launch/gov_report"
DATASET_REVISION = "32feeaede49fed993aef070bc4da09263fd0429a"

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"

CACHE = "/tmp/itiapkin/spark-llm/hf-cache"
CHUNK_SIZE = 2048

OUT_DIR = Path(__file__).resolve().parent.parent / "evidence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUT_DIR / "govreport-token-lengths.csv"
JSON_PATH = OUT_DIR / "govreport-token-audit.json"


def recursive_load(section, keep_letter=False, depth=0):
    sections = []

    if section["section_title"] != "Letter" or keep_letter:
        sections.append({
            "title": " ".join(section["section_title"].strip().split()),
            "paragraphs": "\n".join(
                " ".join(paragraph.strip().split())
                for paragraph in section["paragraphs"]
            ),
            "depth": depth,
        })

        for subsection in section["subsections"]:
            sections.extend(
                recursive_load(subsection, keep_letter, depth + 1)
            )
    else:
        for subsection in section["subsections"]:
            sections.extend(
                recursive_load(subsection, keep_letter, depth)
            )

    return sections


def build_gao_document(data):
    sections = []

    for section in data["report"]:
        sections.extend(
            recursive_load(section, keep_letter=False, depth=1)
        )

    return " ".join(
        section["title"] + " " + section["paragraphs"]
        if section["paragraphs"]
        else section["title"]
        for section in sections
    ).replace("\n", " ").strip()


def build_crs_document(data):
    sections = recursive_load(
        data["reports"],
        keep_letter=True,
        depth=0,
    )

    return " ".join(
        section["title"] + " " + section["paragraphs"]
        if section["paragraphs"]
        else section["title"]
        for section in sections
    ).replace("\n", " ").strip()


tokenizer = AutoTokenizer.from_pretrained(
    MODEL,
    revision=MODEL_REVISION,
    cache_dir=CACHE,
    local_files_only=True,
)

gao_path = hf_hub_download(
    repo_id=DATASET,
    filename="data/gao_train.jsonl",
    repo_type="dataset",
    revision=DATASET_REVISION,
    cache_dir=CACHE,
)

crs_path = hf_hub_download(
    repo_id=DATASET,
    filename="data/crs_train.jsonl",
    repo_type="dataset",
    revision=DATASET_REVISION,
    cache_dir=CACHE,
)

lengths = []
chunk_counts = []
rows = []
hash_counts = Counter()

malformed = 0
empty = 0


def process_file(path, source):
    global malformed, empty

    builder = build_gao_document if source == "GAO" else build_crs_document

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                document = builder(data)
            except Exception as exc:
                malformed += 1
                print(
                    f"MALFORMED {source} line={line_number}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue

            document_id = f"{source}_{data['id']}"

            if not document:
                empty += 1
                continue

            token_count = len(
                tokenizer.encode(
                    document,
                    add_special_tokens=False,
                )
            )

            chunks = math.ceil(token_count / CHUNK_SIZE)

            digest = hashlib.sha256(
                document.encode("utf-8")
            ).hexdigest()

            hash_counts[digest] += 1
            lengths.append(token_count)
            chunk_counts.append(chunks)

            rows.append({
                "id": document_id,
                "source": source,
                "source_tokens": token_count,
                "chunks_2048": chunks,
            })

            if len(rows) % 500 == 0:
                print(f"processed: {len(rows)}")


process_file(gao_path, "GAO")
process_file(crs_path, "CRS")

lengths_np = np.asarray(lengths, dtype=np.int64)
chunks_np = np.asarray(chunk_counts, dtype=np.int64)

percentiles = {
    f"p{p}": float(np.percentile(lengths_np, p))
    for p in [10, 25, 50, 75, 90, 95, 99]
}

thresholds = [2048, 4096, 8192, 16384, 32768]

threshold_counts = {
    f"above_{threshold}": int(np.sum(lengths_np > threshold))
    for threshold in thresholds
}

duplicate_records = sum(
    count - 1
    for count in hash_counts.values()
    if count > 1
)

top_longest = sorted(
    rows,
    key=lambda row: row["source_tokens"],
    reverse=True,
)[:10]

summary = {
    "dataset": DATASET,
    "configuration": "plain_text",
    "dataset_revision": DATASET_REVISION,
    "tokenizer": MODEL,
    "tokenizer_revision": MODEL_REVISION,
    "chunk_size_tokens": CHUNK_SIZE,
    "document_count": int(len(lengths_np)),
    "total_source_tokens": int(lengths_np.sum()),
    "min_tokens": int(lengths_np.min()),
    "max_tokens": int(lengths_np.max()),
    "mean_tokens": float(lengths_np.mean()),
    "median_tokens": float(np.median(lengths_np)),
    "std_tokens_population": float(lengths_np.std(ddof=0)),
    "cv_tokens": float(
        lengths_np.std(ddof=0) / lengths_np.mean()
    ),
    "percentiles": percentiles,
    "threshold_counts": threshold_counts,
    "total_chunks_2048": int(chunks_np.sum()),
    "mean_chunks_per_document": float(chunks_np.mean()),
    "max_chunks_per_document": int(chunks_np.max()),
    "malformed_records": malformed,
    "empty_records": empty,
    "exact_duplicate_records_beyond_first": duplicate_records,
    "top_10_longest_documents": top_longest,
}

with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "id",
            "source",
            "source_tokens",
            "chunks_2048",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print()
print("=== GOVREPORT TOKEN AUDIT ===")
print(json.dumps(summary, indent=2))
print()
print("CSV:", CSV_PATH)
print("JSON:", JSON_PATH)
print("GOVREPORT_TOKEN_AUDIT_OK")
