"""Run the frozen tree-aligned agent on the 382-case population sample."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pandas as pd

import run_openai_sol_90_agentic as base


ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()
SAMPLE = ROOT / "data" / "final" / "population_sample_382" / "specpath_population_sample_382.csv"
POPULATION_CACHE = ROOT / "outputs" / "population_1200_anchor_evidence" / "git_cache"
base.SOURCE = SAMPLE
base.PROMPT_FILE = ROOT / "validation" / "LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md"
base.PROTOCOL_FILE = ROOT / "validation" / "OPENAI_SOL_POPULATION_382_AGENTIC_PROTOCOL.md"
base.DEFAULT_OUTPUT = ROOT / "outputs" / "openai_sol_population_382_agentic"
base.GIT_CACHE = POPULATION_CACHE


def repo_cache_path(repo: str) -> Path:
    return POPULATION_CACHE / re.sub(r"[^A-Za-z0-9_.-]+", "__", repo)


class PopulationRepositoryTools(base.RepositoryTools):
    def __init__(self, case: dict[str, Any]):
        self.case = case
        self.review_id = case["review_id"]
        self.repo_dir = repo_cache_path(case["repo_name"])
        self.anchor = case["anchor_sha"]
        self.repo_name = case["repo_name"]
        self.anchor_available = False
        self.access_error = ""
        if not (self.repo_dir / "HEAD").exists():
            self.tree = []
            self.tree_set = set()
            self.access_error = "frozen_git_cache_missing"
            return
        check = base.run_git(self.repo_dir, ["cat-file", "-e", f"{self.anchor}^{{commit}}"], timeout=30)
        if check.returncode != 0:
            self.tree = []
            self.tree_set = set()
            self.access_error = "anchor_commit_unavailable_in_frozen_cache"
            return
        tree_result = base.run_git(self.repo_dir, ["ls-tree", "-r", "--name-only", self.anchor], timeout=120)
        if tree_result.returncode != 0:
            self.tree = []
            self.tree_set = set()
            self.access_error = "anchor_tree_unreadable"
            return
        self.tree = [line for line in tree_result.stdout.splitlines() if line]
        self.tree_set = set(self.tree)
        self.anchor_available = True


def load_cases() -> list[dict[str, Any]]:
    frame = pd.read_csv(SAMPLE)
    if len(frame) != 382 or frame.sample_id.nunique() != 382:
        raise ValueError("Expected the frozen 382-case population sample")
    if frame.classification.notna().any() or frame.classification_source.notna().any():
        raise ValueError("Population sample contains prohibited semantic labels")
    cases = []
    for row in frame.where(pd.notna(frame), "").to_dict("records"):
        cases.append(
            {
                "review_id": str(row["sample_id"]),
                "repo_name": str(row["repo_name"]),
                "anchor_sha": str(row["anchor_sha"]),
                "artifact_path": str(row["artifact_path"]),
                "code_path": str(row["code_path"]),
                "resolved_path": str(row.get("resolved_path", "")),
                "task_url": str(row.get("task_url", "")),
                "literal_path_url": str(row.get("literal_path_url", "")),
                "anchor_path": "",
                "anchor_path_url": "",
                "task_context": "",
            }
        )
    return cases


original_manifest_payload = base.manifest_payload


def manifest_payload(output_dir: Path, enable_web: bool) -> dict[str, Any]:
    payload = original_manifest_payload(output_dir, enable_web)
    payload["version"] = "population_382_agentic_tree_aligned_v2"
    payload["records"] = 382
    payload["development_data"] = False
    payload["starting_information"] = "label-free frozen probability-sample record"
    payload["repository_access"]["git_cache"] = base.safe_rel(POPULATION_CACHE)
    payload["files"][base.safe_rel(THIS_FILE)] = hashlib.sha256(THIS_FILE.read_bytes()).hexdigest()
    return payload


base.RepositoryTools = PopulationRepositoryTools
base.load_cases = load_cases
base.manifest_payload = manifest_payload


if __name__ == "__main__":
    base.main()
