"""Run the tree-aligned V2 agentic review without modifying the frozen V1."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import run_openai_sol_90_agentic as base


ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()
base.PROMPT_FILE = ROOT / "validation" / "LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md"
base.PROTOCOL_FILE = ROOT / "validation" / "OPENAI_SOL_90_AGENTIC_V2_PROTOCOL.md"
base.DEFAULT_OUTPUT = ROOT / "outputs" / "openai_sol_90_agentic_v2"

original_manifest_payload = base.manifest_payload


def manifest_payload(output_dir: Path, enable_web: bool) -> dict[str, Any]:
    payload = original_manifest_payload(output_dir, enable_web)
    payload["version"] = "agentic_v2_tree_aligned_temporal_invalidity"
    payload["files"][base.safe_rel(THIS_FILE)] = hashlib.sha256(THIS_FILE.read_bytes()).hexdigest()
    return payload


base.manifest_payload = manifest_payload


if __name__ == "__main__":
    base.main()
