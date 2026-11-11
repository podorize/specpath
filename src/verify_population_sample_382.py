"""Verify the released, frozen 382-reference probability sample.

The upstream SpecMine frame is not redistributed. This checks the released
sample's integrity, stratum allocation, pre-evidence ranks, and design weights;
it does not claim to redraw the sample from an unavailable frame.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data" / "final" / "population_sample_382"
MANIFEST = DIRECTORY / "specpath_population_sample_382_manifest.json"
STRATA = {0: "open_missing", 1: "completed_missing"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sample_path = ROOT / manifest["output_csv"]
    parquet_path = ROOT / manifest["output_parquet"]
    if sha256(sample_path) != manifest["output_csv_sha256"]:
        raise ValueError("Frozen sample CSV hash changed")
    if parquet_path.is_file() and sha256(parquet_path) != manifest["output_parquet_sha256"]:
        raise ValueError("Frozen sample Parquet hash changed")

    sample = pd.read_csv(sample_path)
    if len(sample) != manifest["sample_n"] or sample.id.nunique() != len(sample):
        raise ValueError("Unexpected number of reference units")
    if sample.sample_id.nunique() != len(sample):
        raise ValueError("Duplicate model case ID")
    if sample.repo_name.nunique() != manifest["sample_repositories"]:
        raise ValueError("Repository count changed")
    if sample.sample_hash.nunique() != len(sample):
        raise ValueError("Random-rank tie or duplicate hash")
    if sample.classification.notna().any() or sample.classification_source.notna().any():
        raise ValueError("Semantic labels appear in the frozen sample")
    if set(sample.task_done.unique()) != set(STRATA):
        raise ValueError("Task-status strata changed")

    for status, name in STRATA.items():
        stratum = sample.loc[sample.task_done.eq(status)]
        population_n = manifest["strata"][name]["population_n"]
        sample_n = manifest["strata"][name]["sample_n"]
        if len(stratum) != sample_n:
            raise ValueError(f"Unexpected allocation in {name}")
        expected_ranks = list(range(1, sample_n + 1))
        if sorted(stratum.rank_within_stratum.tolist()) != expected_ranks:
            raise ValueError(f"Random ranks changed in {name}")
        if sorted(stratum.subsample_rank_within_stratum.tolist()) != expected_ranks:
            raise ValueError(f"Released selection ranks changed in {name}")
        expected = {
            "frame_size": population_n,
            "stratum_sample_size": sample_n,
            "inclusion_probability": sample_n / population_n,
            "sampling_weight": population_n / sample_n,
        }
        for column, value in expected.items():
            if not all(math.isclose(float(actual), value, rel_tol=1e-12) for actual in stratum[column]):
                raise ValueError(f"{column} changed in {name}")

    if sum(item["population_n"] for item in manifest["strata"].values()) != manifest["population_n"]:
        raise ValueError("Population stratum sizes do not add up")
    if int(sample.prior_development_overlap.sum()) != manifest["prior_development_overlap_n"]:
        raise ValueError("Development overlap count changed")
    print(json.dumps({"sample_n": len(sample), "repositories": sample.repo_name.nunique(),
                      "strata": {name: manifest["strata"][name]["sample_n"] for name in STRATA.values()},
                      "csv_sha256": sha256(sample_path)}, indent=2))


if __name__ == "__main__":
    main()
