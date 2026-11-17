"""Build curated, anonymous advisor and replication archives."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from redact_public_release import TEXT_SUFFIXES, redact_bytes, remaining_direct_identifiers


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PAPER_FILES = [
    "paper/main.tex",
    "paper/README.md",
    "paper/IEEEtran.cls",
    "paper/references.bib",
    "paper/figures/decision_flow_compact.png",
    "paper/figures/decision_flow_compact.svg",
]
REPLICATION_FILES = [
    "README.md",
    "pyproject.toml",
    "uv.lock",
    *PAPER_FILES,
    "validation/study_protocol.md",
    "validation/reproduction_guide.md",
    "validation/gold_90_run_protocol.md",
    "validation/protocol_amendment.json",
    "validation/silver_382_run_protocol.md",
    "validation/llm_classification_prompt.md",
    "validation/classification_examples.md",
    "validation/llm_output_schema.json",
    "data/specpath_gold_human_90.csv",
    "data/specpath_gold_human_90_manifest.json",
    "data/interim/validation_final_90_en.csv",
    "data/population_sample_382/specpath_population_sample_382.csv",
    "data/population_sample_382/specpath_population_sample_382_manifest.json",
    "outputs/90_agentic/predictions.jsonl",
    "outputs/90_agentic/frozen_manifest.json",
    "outputs/population_382_agentic/predictions.jsonl",
    "outputs/population_382_agentic/frozen_manifest.json",
    "src/verify_population_sample_382.py",
    "src/run_openai_sol_population_382_agentic.py",
    "src/run_openai_sol_90_agentic.py",
    "src/run_openai_sol_90_agentic_v2.py",
    "src/analyze_population_382_agentic.py",
    "src/analyze_gold_comparison.py",
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
    amendment = json.loads((ROOT / "validation/protocol_amendment.json").read_text(encoding="utf-8"))
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
        if relative in {
            "src/run_openai_sol_90_agentic.py",
            "src/run_openai_sol_90_agentic_v2.py",
            "src/run_openai_sol_population_382_agentic.py",
        }:
            original = path.read_bytes()
            for current, frozen in (
                (b"llm_classification_prompt.md", b"LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md"),
                (b"gold_90_run_protocol.md", b"OPENAI_SOL_90_AGENTIC_V2_PROTOCOL.md"),
                (b"silver_382_run_protocol.md", b"OPENAI_SOL_POPULATION_382_AGENTIC_PROTOCOL.md"),
                (b"llm_output_schema.json", b"llm_judge_output_schema_openai_agentic.json"),
            ):
                original = original.replace(current, frozen)
            if relative == "src/run_openai_sol_90_agentic.py":
                original = original.replace(
                    b"LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md",
                    b"LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC.md",
                ).replace(
                    b"OPENAI_SOL_90_AGENTIC_V2_PROTOCOL.md",
                    b"OPENAI_SOL_90_AGENTIC_PROTOCOL.md",
                )
            frozen_output_names = {
                "src/run_openai_sol_90_agentic.py": b'"openai_sol_90_agentic"',
                "src/run_openai_sol_90_agentic_v2.py": b'"openai_sol_90_agentic_v2"',
                "src/run_openai_sol_population_382_agentic.py": b'"openai_sol_population_382_agentic"',
            }
            current_output_name = (
                b'"population_382_agentic"'
                if relative == "src/run_openai_sol_population_382_agentic.py"
                else b'"90_agentic"'
            )
            original = original.replace(current_output_name, frozen_output_names[relative])
            if hashlib.sha256(original).hexdigest() == expected_sha256:
                continue
        if relative == "data/population_sample_382/specpath_population_sample_382.csv":
            sample_manifest = json.loads((ROOT / "data/population_sample_382/specpath_population_sample_382_manifest.json").read_text(encoding="utf-8"))
            if actual_sha256 != sample_manifest["output_csv_sha256"]:
                raise ValueError(f"Frozen input missing or changed: {relative}")
            classified_path = ROOT / "results/population_382_agentic/classified_sample_382.csv"
            with classified_path.open(newline="", encoding="utf-8") as classified_source:
                classified = {row["sample_id"]: row for row in csv.DictReader(classified_source)}
            with path.open(newline="", encoding="utf-8") as source:
                reader = csv.DictReader(source)
                fieldnames = list(reader.fieldnames or [])
                removed_columns = ["prior_development_overlap", "prior_development_sources"]
                if any(column in fieldnames for column in removed_columns):
                    raise ValueError("Released sample still contains removed columns")
                insertion = fieldnames.index("sampling_stratum")
                fieldnames[insertion:insertion] = removed_columns
                recovered = io.StringIO(newline="")
                writer = csv.DictWriter(recovered, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                for row in reader:
                    historical = classified.get(row["sample_id"])
                    if historical is None:
                        raise ValueError("Missing original sample provenance")
                    for column in removed_columns:
                        row[column] = historical[column]
                    writer.writerow(row)
            if hashlib.sha256(recovered.getvalue().encode("utf-8")).hexdigest() == expected_sha256:
                continue
        raise ValueError(f"Frozen input missing or changed: {relative}")


def main() -> None:
    verify_frozen_inputs("outputs/90_agentic/frozen_manifest.json")
    verify_frozen_inputs("outputs/population_382_agentic/frozen_manifest.json")
    DIST.mkdir(exist_ok=True)
    replication = REPLICATION_FILES.copy()
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "results/population_382_agentic").iterdir())
        if path.is_file()
    )
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "results/90_agentic").iterdir())
        if path.is_file()
    )
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "outputs/90_agentic/traces").glob("*.jsonl"))
    )
    replication.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "outputs/population_382_agentic/traces").glob("*.jsonl"))
    )
    if len([path for path in replication if path.startswith("outputs/population_382_agentic/traces/")]) != 382:
        raise ValueError("Expected exactly 382 case traces")
    result = {
        "paper": write_archive("specpath_msr2027_overleaf_current.zip", PAPER_FILES),
        "replication": write_archive("specpath_msr2027_anonymous_replication_candidate.zip", replication, redact=True),
    }
    (DIST / "bundle_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: {"archive": item["archive"], "files": len(item["files"]), "sha256": item["sha256"]} for name, item in result.items()}, indent=2))


if __name__ == "__main__":
    main()
