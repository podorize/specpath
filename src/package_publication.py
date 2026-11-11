"""Build curated, anonymous advisor and replication archives."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from redact_public_release import TEXT_SUFFIXES, redact_bytes, remaining_direct_identifiers


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PAPER_FILES = [
    "paper/main.tex",
    "paper/IEEEtran.cls",
    "paper/references.bib",
    "paper/figures/decision_tree_compact.pdf",
]
REPLICATION_FILES = [
    "README.md",
    "pyproject.toml",
    "PUBLICATION_READINESS.md",
    *PAPER_FILES,
    "paper/figures/final_decision_tree.svg",
    "paper/figures/decision_tree_compact.svg",
    "paper/figures/generate_compact_tree.py",
    "validation/ACTIVE_STUDY_PROTOCOL.md",
    "validation/REPRODUCE_FINAL_STUDY.md",
    "validation/OPENAI_SOL_90_AGENTIC_V2_PROTOCOL.md",
    "validation/PROTOCOL_RECORD_AMENDMENT.json",
    "validation/OPENAI_SOL_POPULATION_382_AGENTIC_PROTOCOL.md",
    "validation/LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md",
    "validation/DECISION_TREE_CASE_EXAMPLES.md",
    "validation/METHODOLOGICAL_REVIEW_7_CASES.md",
    "validation/llm_judge_output_schema_openai_agentic.json",
    "data/final/specpath_gold_human_90.csv",
    "data/final/specpath_gold_human_90_manifest.json",
    "data/interim/validation_final_90_en.csv",
    "data/final/population_sample_382/specpath_population_sample_382.csv",
    "data/final/population_sample_382/specpath_population_sample_382_manifest.json",
    "outputs/openai_sol_90_agentic_v2/predictions.jsonl",
    "outputs/openai_sol_90_agentic_v2/frozen_manifest.json",
    "outputs/openai_sol_population_382_agentic/predictions.jsonl",
    "outputs/openai_sol_population_382_agentic/frozen_manifest.json",
    "src/verify_population_sample_382.py",
    "src/run_openai_sol_population_382_agentic.py",
    "src/run_openai_sol_90_agentic.py",
    "src/run_openai_sol_90_agentic_v2.py",
    "src/analyze_population_382_agentic.py",
    "src/redact_public_release.py",
]
FORBIDDEN = (
    b"sk-proj-",
    b"ghp_",
    b"github_pat_",
    b"AKIA",
    b"xoxb-",
    b"AIza",
    b"-----BEGIN PRIVATE KEY-----",
    b"/Users/pedroodorize",
    b"pedroodorize",
    b"Pedro Odorize",
    b"@gmail.com",
)


def write_member(handle: ZipFile, name: str, data: bytes) -> None:
    """Use fixed ZIP metadata so identical source files yield identical archives."""
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o644 << 16
    info.compress_type = ZIP_DEFLATED
    handle.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)


def write_archive(name: str, files: list[str], *, redact: bool = False) -> dict:
    archive = DIST / name
    manifest = {}
    redactions = {}
    previous_redactions = {}
    record_path = DIST / "RELEASE_REDACTIONS.json"
    if redact and record_path.is_file():
        previous_redactions = json.loads(record_path.read_text(encoding="utf-8"))["changed_files"]
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as handle:
        for relative in sorted(set(files)):
            path = ROOT / relative
            data = path.read_bytes()
            original_sha256 = hashlib.sha256(data).hexdigest()
            if redact and path.suffix.lower() in TEXT_SUFFIXES:
                data, counts = redact_bytes(data)
                if sum(counts.values()):
                    redactions[relative] = {
                        "original_sha256": original_sha256,
                        "released_sha256": hashlib.sha256(data).hexdigest(),
                        "counts": counts,
                    }
                elif (
                    relative in previous_redactions
                    and original_sha256 == previous_redactions[relative]["released_sha256"]
                ):
                    redactions[relative] = previous_redactions[relative]
                remaining = remaining_direct_identifiers(data)
                if any(remaining.values()):
                    raise ValueError(f"Direct identifier remains in {relative}: {remaining}")
            matches = [token.decode() for token in FORBIDDEN if token in data]
            if matches:
                raise ValueError(f"Potential identity or credential in {relative}: {matches}")
            write_member(handle, relative, data)
            manifest[relative] = hashlib.sha256(data).hexdigest()
        if redact:
            release_record = {
                "purpose": "anonymous-review privacy redaction; original run files remain frozen internally",
                "rules": ["email-like strings -> [EMAIL_REDACTED]", "user-home path segments -> REDACTED_USER"],
                "changed_files": redactions,
            }
            record_data = (json.dumps(release_record, indent=2) + "\n").encode("utf-8")
            write_member(handle, "RELEASE_REDACTIONS.json", record_data)
            manifest["RELEASE_REDACTIONS.json"] = hashlib.sha256(record_data).hexdigest()
            record_path.write_bytes(record_data)
    return {"archive": archive.name, "files": manifest, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}


def verify_frozen_inputs(manifest_path: str) -> None:
    manifest = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
    amendment = json.loads((ROOT / "validation/PROTOCOL_RECORD_AMENDMENT.json").read_text(encoding="utf-8"))
    redactions = json.loads((DIST / "RELEASE_REDACTIONS.json").read_text(encoding="utf-8"))["changed_files"]
    for relative, expected_sha256 in manifest["files"].items():
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"Frozen input missing or changed: {relative}")
        actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha256 == expected_sha256:
            continue
        release_record = redactions.get(relative)
        if (
            release_record
            and expected_sha256 == release_record["original_sha256"]
            and actual_sha256 == release_record["released_sha256"]
        ):
            continue
        if (
            relative == amendment["document"]
            and expected_sha256 == amendment["original_manifest_sha256"]
            and actual_sha256 == amendment["amended_sha256"]
        ):
            continue
        raise ValueError(f"Frozen input missing or changed: {relative}")


def main() -> None:
    verify_frozen_inputs("outputs/openai_sol_90_agentic_v2/frozen_manifest.json")
    verify_frozen_inputs("outputs/openai_sol_population_382_agentic/frozen_manifest.json")
    DIST.mkdir(exist_ok=True)
    replication = REPLICATION_FILES.copy()
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "results/population_382_agentic").iterdir())
        if path.is_file()
    )
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "results/validation/openai_sol_90_agentic_v2").iterdir())
        if path.is_file()
    )
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "outputs/openai_sol_90_agentic_v2/traces").glob("*.jsonl"))
    )
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "outputs/openai_sol_population_382_agentic/traces").glob("*.jsonl"))
    )
    if len([path for path in replication if path.startswith("outputs/openai_sol_population_382_agentic/traces/")]) != 382:
        raise ValueError("Expected exactly 382 case traces")
    result = {
        "paper": write_archive("specpath_msr2027_overleaf_current.zip", PAPER_FILES),
        "replication": write_archive("specpath_msr2027_anonymous_replication_candidate.zip", replication, redact=True),
    }
    (DIST / "bundle_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: {"archive": item["archive"], "files": len(item["files"]), "sha256": item["sha256"]} for name, item in result.items()}, indent=2))


if __name__ == "__main__":
    main()
