"""Freeze a 382-reference nested probability sample from the 1,200 frame.

The parent sample's within-stratum random ranks were frozen before evidence or
labels. Taking the first 130 open and 252 completed ranks therefore creates a
reproducible probability sample without consulting access or semantic results.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "data" / "final" / "population_sample_1200" / "specpath_population_sample_1200.csv"
PARENT_MANIFEST = ROOT / "data" / "final" / "population_sample_1200" / "specpath_population_sample_1200_manifest.json"
OUT_DIR = ROOT / "data" / "final" / "population_sample_382"
OUT_CSV = OUT_DIR / "specpath_population_sample_382.csv"
OUT_PARQUET = OUT_DIR / "specpath_population_sample_382.parquet"
MANIFEST = OUT_DIR / "specpath_population_sample_382_manifest.json"
ALLOCATION = {0: 130, 1: 252}
POPULATION = {0: 17_752, 1: 34_227}
EXPECTED_PARENT_HASH = "09048574d5a0e8aea3ca8f300505d6ebc839f4d24772d84b2eda6e37e891160b"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha256(PARENT) != EXPECTED_PARENT_HASH:
        raise ValueError("Frozen 1,200-case parent sample hash changed")
    parent_manifest = json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))
    frame = pd.read_csv(PARENT)
    if len(frame) != 1_200 or frame.sample_id.nunique() != 1_200:
        raise ValueError("Expected the frozen 1,200-case parent sample")
    if frame.classification.notna().any() or frame.classification_source.notna().any():
        raise ValueError("Parent sample unexpectedly contains semantic labels")

    parts = []
    for task_done, sample_n in ALLOCATION.items():
        selected = (
            frame[frame.task_done == task_done]
            .sort_values(["rank_within_stratum", "id"])
            .head(sample_n)
            .copy()
        )
        if len(selected) != sample_n:
            raise ValueError(f"Insufficient parent rows for stratum {task_done}")
        selected["parent_sample_id"] = selected["sample_id"]
        selected["frame_size"] = POPULATION[task_done]
        selected["stratum_sample_size"] = sample_n
        selected["inclusion_probability"] = sample_n / POPULATION[task_done]
        selected["sampling_weight"] = POPULATION[task_done] / sample_n
        selected["subsample_rank_within_stratum"] = range(1, sample_n + 1)
        parts.append(selected)

    sample = pd.concat(parts, ignore_index=True).sort_values(["sample_hash", "id"]).reset_index(drop=True)
    sample.insert(0, "subsample_id", [f"M{i:04d}" for i in range(1, len(sample) + 1)])
    if len(sample) != 382 or sample.id.nunique() != 382:
        raise AssertionError("Expected 382 unique population units")
    if sample.groupby("task_done").size().to_dict() != ALLOCATION:
        raise AssertionError("Unexpected 382-case allocation")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample.to_csv(OUT_CSV, index=False)
    sample.to_parquet(OUT_PARQUET, index=False)
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "population_sample_382_frozen_before_labels",
        "target_population": parent_manifest["target_population"],
        "population_n": 51_979,
        "population_repositories": parent_manifest["population_repositories"],
        "sample_n": 382,
        "sample_repositories": int(sample.repo_name.nunique()),
        "confidence_level": 0.95,
        "conservative_population_proportion": 0.5,
        "finite_population_maximum_margin_of_error": 0.05002305824660837,
        "parent_sample": str(PARENT.relative_to(ROOT)),
        "parent_sample_sha256": sha256(PARENT),
        "parent_sampling_seed": parent_manifest["seed"],
        "selection_rule": (
            "Nested cut of the parent sample's pre-evidence random rank: first 130 open_missing "
            "and first 252 completed_missing records."
        ),
        "semantic_class_used_for_sampling": False,
        "access_or_evidence_status_used_for_sampling": False,
        "model_prediction_used_for_sampling": False,
        "replacement_or_class_complement": False,
        "strata": {
            "open_missing": {"population_n": POPULATION[0], "sample_n": ALLOCATION[0]},
            "completed_missing": {"population_n": POPULATION[1], "sample_n": ALLOCATION[1]},
        },
        "prior_development_overlap_n": int(sample.prior_development_overlap.sum()),
        "prior_overlap_policy": parent_manifest["prior_overlap_policy"],
        "output_csv": str(OUT_CSV.relative_to(ROOT)),
        "output_csv_sha256": sha256(OUT_CSV),
        "output_parquet": str(OUT_PARQUET.relative_to(ROOT)),
        "output_parquet_sha256": sha256(OUT_PARQUET),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
