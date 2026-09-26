import json
from pathlib import Path

import numpy as np
import pandas as pd

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "evidence"

INPUT = EVIDENCE_DIR / "govreport-token-lengths.csv"
OUTPUT = EVIDENCE_DIR / "govreport-workload-feasibility.json"

N = 300
GAO_N = 188
CRS_N = 112
SEED = 20260926

TARGET_MEAN = 10171.503225069924
TARGET_TOTAL = TARGET_MEAN * N

rng = np.random.default_rng(SEED)

df = pd.read_csv(INPUT)


def stats(frame):
    x = frame["source_tokens"].to_numpy(dtype=np.float64)

    return {
        "documents": int(len(x)),
        "gao": int((frame["source"] == "GAO").sum()),
        "crs": int((frame["source"] == "CRS").sum()),
        "total_tokens": int(x.sum()),
        "mean_tokens": float(x.mean()),
        "min_tokens": int(x.min()),
        "max_tokens": int(x.max()),
        "std_tokens": float(x.std(ddof=0)),
        "cv": float(x.std(ddof=0) / x.mean()),
    }


def sample_source(pool, source, n):
    source_pool = pool[pool["source"] == source]

    if len(source_pool) < n:
        raise RuntimeError(
            f"Not enough {source} documents: "
            f"need {n}, have {len(source_pool)}"
        )

    indices = rng.choice(
        source_pool.index.to_numpy(),
        size=n,
        replace=False,
    )

    return source_pool.loc[indices]


def search(pool, target_cv, trials=20000):
    best = None
    best_score = float("inf")

    for _ in range(trials):
        candidate = pd.concat(
            [
                sample_source(pool, "GAO", GAO_N),
                sample_source(pool, "CRS", CRS_N),
            ],
            ignore_index=True,
        )

        s = stats(candidate)

        total_error = abs(
            s["total_tokens"] - TARGET_TOTAL
        ) / TARGET_TOTAL

        cv_error = abs(s["cv"] - target_cv)

        score = total_error * 10 + cv_error

        if score < best_score:
            best_score = score
            best = candidate.copy()

    return best


# Low variability:
# documents concentrated near the corpus mean.
low_pool = df[
    (df["source_tokens"] >= 7500)
    & (df["source_tokens"] <= 13000)
]

# Moderate variability:
# much wider natural range.
moderate_pool = df[
    (df["source_tokens"] >= 3500)
    & (df["source_tokens"] <= 20000)
]

# High variability:
# deliberately mix naturally short and long documents.
high_pool = df[
    (df["source_tokens"] <= 6000)
    | (
        (df["source_tokens"] >= 15000)
        & (df["source_tokens"] <= 40000)
    )
]

workloads = {
    "low": search(low_pool, target_cv=0.15),
    "moderate": search(moderate_pool, target_cv=0.45),
    "high": search(high_pool, target_cv=0.80),
}

result = {
    "purpose": "GovReport workload-construction feasibility check",
    "documents_per_workload": N,
    "gao_per_workload": GAO_N,
    "crs_per_workload": CRS_N,
    "target_total_tokens": int(round(TARGET_TOTAL)),
    "seed": SEED,
    "workloads": {},
}

for name, workload in workloads.items():
    s = stats(workload)

    s["total_token_difference_pct"] = float(
        100
        * (s["total_tokens"] - TARGET_TOTAL)
        / TARGET_TOTAL
    )

    result["workloads"][name] = s

    workload[
        ["id", "source", "source_tokens", "chunks_2048"]
    ].sort_values("source_tokens").to_csv(
        OUTPUT.parent / f"govreport-workload-{name}.csv",
        index=False,
    )

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("=== GOVREPORT WORKLOAD FEASIBILITY ===")
print(json.dumps(result, indent=2))
print()

cvs = [
    result["workloads"]["low"]["cv"],
    result["workloads"]["moderate"]["cv"],
    result["workloads"]["high"]["cv"],
]

if not (cvs[0] < cvs[1] < cvs[2]):
    raise RuntimeError("CV levels are not ordered low < moderate < high")

print("GOVREPORT_WORKLOAD_FEASIBILITY_OK")
