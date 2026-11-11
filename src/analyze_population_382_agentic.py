"""Analyze the frozen 382-case agentic probability sample."""

from __future__ import annotations

import glob
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from jsonschema import validate as validate_json_schema


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "final" / "population_sample_382" / "specpath_population_sample_382.csv"
SAMPLE_MANIFEST = ROOT / "data" / "final" / "population_sample_382" / "specpath_population_sample_382_manifest.json"
OUTPUT = ROOT / "outputs" / "openai_sol_population_382_agentic"
PREDICTIONS = OUTPUT / "predictions.jsonl"
RUN_MANIFEST = OUTPUT / "frozen_manifest.json"
TRACES = OUTPUT / "traces"
SCHEMA = ROOT / "validation" / "llm_judge_output_schema_openai_agentic.json"
RESULTS = ROOT / "results" / "population_382_agentic"
N_POPULATION = 51_979
Z = 1.959963984540054

TAXONOMY = [
    "confirmed_exists",
    "confirmed_missing_problematic",
    "expected_absence_create",
    "expected_absence_move_or_delete",
    "external_repository_reference",
    "non_file_reference",
    "ambiguous_reference",
    "inaccessible_or_invalid",
]
INTERPRETIVE_GROUPS = {
    "expected_lifecycle_change": ("expected_absence_create", "expected_absence_move_or_delete"),
    "scope_or_non_file": ("external_repository_reference", "non_file_reference"),
    "inaccessible_or_ambiguous": ("inaccessible_or_invalid", "ambiguous_reference"),
    "problematic_absence": ("confirmed_missing_problematic",),
    "exists_after_resolution": ("confirmed_exists",),
}
ABSTAIN = {"ambiguous_reference", "inaccessible_or_invalid"}
PROHIBITED = {
    "classification",
    "classification_source",
    "gold_human_classification",
    "manual_classification",
    "exists_at_anchor",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson_interval(proportion: float, effective_n: float) -> tuple[float, float]:
    if effective_n <= 0:
        return 0.0, 1.0
    denominator = 1 + Z * Z / effective_n
    center = (proportion + Z * Z / (2 * effective_n)) / denominator
    half = (
        Z
        * math.sqrt(proportion * (1 - proportion) / effective_n + Z * Z / (4 * effective_n * effective_n))
        / denominator
    )
    return max(0.0, center - half), min(1.0, center + half)


def load_predictions() -> pd.DataFrame:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    rows = []
    for line in PREDICTIONS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        validate_json_schema({key: raw[key] for key in schema["required"]}, schema)
        usage = raw.pop("usage")
        raw["input_tokens"] = int(usage.get("input_tokens", 0))
        raw["output_tokens"] = int(usage.get("output_tokens", 0))
        raw["total_tokens"] = int(usage.get("total_tokens", 0))
        raw["tool_names_json"] = json.dumps(raw.pop("tool_names"), ensure_ascii=False)
        raw["evidence_paths_json"] = json.dumps(raw.pop("evidence_paths"), ensure_ascii=False)
        raw["missing_evidence_json"] = json.dumps(raw.pop("missing_evidence"), ensure_ascii=False)
        rows.append(raw)
    frame = pd.DataFrame(rows)
    if len(frame) != 382 or frame.review_id.nunique() != 382:
        raise ValueError("Expected 382 unique predictions")
    return frame


def trace_audit(sample: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame, dict[str, int]]:
    expected_artifact = sample.set_index("sample_id").artifact_path.to_dict()
    rows = []
    tokens = {"input": 0, "cached": 0, "cache_write": 0, "uncached": 0, "output": 0, "responses": 0}
    for sample_id in sample.sample_id:
        trace = TRACES / f"{sample_id}.jsonl"
        events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line.strip()]
        starts = [event for event in events if event.get("event") == "case_start"]
        completes = [event for event in events if event.get("event") == "case_complete"]
        if len(starts) != 1 or len(completes) != 1:
            raise ValueError(f"Incomplete trace for {sample_id}")
        leaked = sorted(PROHIBITED.intersection(starts[0]["case"]))
        function_events = [event for event in events if event.get("event") == "function_result"]
        artifact_reads = [
            event
            for event in function_events
            if event.get("name") == "read_file"
            and event.get("arguments", {}).get("path") == expected_artifact[sample_id]
        ]
        web_calls = 0
        for event in events:
            if event.get("event") != "model_response":
                continue
            usage = event.get("usage") or {}
            details = usage.get("input_tokens_details") or {}
            input_tokens = int(usage.get("input_tokens", 0))
            cached = int(details.get("cached_tokens", 0))
            cache_write = int(details.get("cache_write_tokens", 0))
            tokens["input"] += input_tokens
            tokens["cached"] += cached
            tokens["cache_write"] += cache_write
            tokens["uncached"] += max(0, input_tokens - cached - cache_write)
            tokens["output"] += int(usage.get("output_tokens", 0))
            tokens["responses"] += 1
            web_calls += sum(item.get("type") == "web_search_call" for item in event.get("output", []))
        rows.append(
            {
                "sample_id": sample_id,
                "trace_complete": True,
                "label_field_leakage": json.dumps(leaked),
                "artifact_read_attempted": bool(artifact_reads),
                "artifact_read_status": artifact_reads[0]["result"].get("status") if artifact_reads else "not_attempted",
                "function_calls": len(function_events),
                "web_calls": web_calls,
                "function_names": json.dumps([event.get("name") for event in function_events]),
            }
        )
    audit = pd.DataFrame(rows)
    summary = {
        "complete_traces": int(audit.trace_complete.sum()),
        "traces_with_label_leakage": int((audit.label_field_leakage != "[]").sum()),
        "artifact_read_attempted": int(audit.artifact_read_attempted.sum()),
        "artifact_read_found": int((audit.artifact_read_status == "found").sum()),
        "artifact_read_anchor_unavailable": int((audit.artifact_read_status == "anchor_unavailable").sum()),
        "artifact_read_not_found_at_anchor": int((audit.artifact_read_status == "not_found_at_anchor").sum()),
        "function_calls": int(audit.function_calls.sum()),
        "web_calls": int(audit.web_calls.sum()),
        "cases_using_web": int((audit.web_calls > 0).sum()),
    }
    return summary, audit, tokens


def distribution(frame: pd.DataFrame) -> pd.DataFrame:
    total_weight = frame.sampling_weight.sum()
    effective_n = total_weight * total_weight / (frame.sampling_weight.pow(2).sum())
    rows = []
    for label in TAXONOMY:
        indicator = (frame.classification == label).astype(float)
        weighted_total = float((indicator * frame.sampling_weight).sum())
        proportion = weighted_total / N_POPULATION
        variance = 0.0
        for _, group in frame.groupby("task_done"):
            n_h = len(group)
            N_h = int(group.frame_size.iloc[0])
            y = (group.classification == label).astype(float)
            p_h = float(y.mean())
            s2_h = float(y.var(ddof=1)) if n_h > 1 else 0.0
            variance += (N_h / N_POPULATION) ** 2 * (1 - n_h / N_h) * s2_h / n_h
        se = math.sqrt(max(0.0, variance))
        normal_low, normal_high = max(0.0, proportion - Z * se), min(1.0, proportion + Z * se)
        wilson_low, wilson_high = wilson_interval(proportion, effective_n)
        rows.append(
            {
                "classification": label,
                "sample_count": int(indicator.sum()),
                "unweighted_proportion": float(indicator.mean()),
                "weighted_population_proportion": proportion,
                "estimated_population_count": weighted_total,
                "design_standard_error": se,
                "design_normal_95_low": normal_low,
                "design_normal_95_high": normal_high,
                "weighted_wilson_95_low": wilson_low,
                "weighted_wilson_95_high": wilson_high,
                "effective_sample_size": effective_n,
            }
        )
    return pd.DataFrame(rows)


def grouped_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, classes in INTERPRETIVE_GROUPS.items():
        selected = frame.classification.isin(classes)
        proportion = float(frame.loc[selected, "sampling_weight"].sum() / N_POPULATION)
        variance = 0.0
        for _, stratum in frame.groupby("task_done"):
            n_h = len(stratum)
            N_h = int(stratum.frame_size.iloc[0])
            values = stratum.classification.isin(classes).astype(float)
            variance += (N_h / N_POPULATION) ** 2 * (1 - n_h / N_h) * float(values.var(ddof=1)) / n_h
        se = math.sqrt(max(0.0, variance))
        rows.append(
            {
                "group": name,
                "classes": ";".join(classes),
                "sample_count": int(selected.sum()),
                "weighted_frame_share": proportion,
                "design_standard_error": se,
                "normal_95_low": max(0.0, proportion - Z * se),
                "normal_95_high": min(1.0, proportion + Z * se),
            }
        )
    result = pd.DataFrame(rows)
    if result.sample_count.sum() != len(frame) or not math.isclose(result.weighted_frame_share.sum(), 1.0):
        raise ValueError("Interpretive groups must partition the probability sample")
    return result


def class_share_contrast(frame: pd.DataFrame, first: str, second: str) -> dict[str, Any]:
    estimate = 0.0
    variance = 0.0
    for _, group in frame.groupby("task_done"):
        n_h = len(group)
        N_h = int(group.frame_size.iloc[0])
        values = (group.classification == first).astype(float) - (group.classification == second).astype(float)
        estimate += (N_h / N_POPULATION) * float(values.mean())
        variance += (N_h / N_POPULATION) ** 2 * (1 - n_h / N_h) * float(values.var(ddof=1)) / n_h
    se = math.sqrt(max(0.0, variance))
    return {
        "contrast": f"{first}_minus_{second}",
        "estimate": estimate,
        "design_standard_error": se,
        "normal_95_low": estimate - Z * se,
        "normal_95_high": estimate + Z * se,
        "interpretation": "exploratory_sampling_only_model_assigned_labels",
    }


def status_share_contrast(frame: pd.DataFrame, label: str) -> dict[str, Any]:
    shares = {}
    variance = 0.0
    for status, group in frame.groupby("task_done"):
        n_h = len(group)
        N_h = int(group.frame_size.iloc[0])
        values = (group.classification == label).astype(float)
        shares[bool(status)] = float(values.mean())
        variance += (1 - n_h / N_h) * float(values.var(ddof=1)) / n_h
    estimate = shares[False] - shares[True]
    se = math.sqrt(max(0.0, variance))
    return {
        "contrast": f"open_minus_completed_{label}",
        "open_share": shares[False],
        "completed_share": shares[True],
        "estimate": estimate,
        "design_standard_error": se,
        "normal_95_low": estimate - Z * se,
        "normal_95_high": estimate + Z * se,
        "interpretation": "exploratory_cross_sectional_sampling_only_model_assigned_labels",
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    sample = pd.read_csv(SAMPLE)
    predictions = load_predictions().rename(columns={"review_id": "sample_id"})
    frame = sample.merge(predictions, on="sample_id", validate="one_to_one")
    if "classification_x" in frame and frame.classification_x.notna().any():
        raise ValueError("Unexpected collision with source classification")
    if "classification_y" in frame:
        frame = frame.drop(columns=["classification_x"]).rename(columns={"classification_y": "classification"})
    elif "classification" not in frame:
        raise ValueError("Prediction classification missing after merge")

    trace_summary, trace_frame, tokens = trace_audit(sample)
    dist = distribution(frame)
    groups = grouped_distribution(frame)
    class_contrasts = pd.DataFrame(
        [
            class_share_contrast(frame, "expected_absence_create", "non_file_reference"),
            class_share_contrast(frame, "expected_absence_create", "expected_absence_move_or_delete"),
            class_share_contrast(frame, "non_file_reference", "expected_absence_move_or_delete"),
        ]
    )
    status_contrasts = pd.DataFrame(
        [
            status_share_contrast(frame, "expected_absence_create"),
            status_share_contrast(frame, "expected_absence_move_or_delete"),
        ]
    )
    by_stratum = (
        frame.groupby(["sampling_stratum", "classification"], observed=False)
        .size()
        .rename("sample_count")
        .reset_index()
    )
    by_stratum["stratum_n"] = by_stratum.sampling_stratum.map(frame.groupby("sampling_stratum").size())
    by_stratum["sample_proportion_within_stratum"] = by_stratum.sample_count / by_stratum.stratum_n

    classifiable = frame[~frame.classification.isin(ABSTAIN)].copy()
    classifiable["conditional_weight"] = classifiable.sampling_weight / classifiable.sampling_weight.sum()
    conditional = (
        classifiable.groupby("classification", observed=False)
        .agg(sample_count=("sample_id", "size"), conditional_weighted_proportion=("conditional_weight", "sum"))
        .reindex(TAXONOMY, fill_value=0)
        .reset_index()
    )
    sensitivity = frame[~frame.prior_development_overlap.astype(bool)].copy()
    sensitivity_dist = distribution(sensitivity.assign(
        sampling_weight=sensitivity.sampling_weight * (N_POPULATION / sensitivity.sampling_weight.sum())
    ))

    run_manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
    start = datetime.fromisoformat(run_manifest["created_at_utc"])
    completed = [datetime.fromisoformat(value) for value in predictions.completed_at_utc]
    elapsed_seconds = (max(completed) - start).total_seconds()
    token_cost = (
        tokens["uncached"] * 2.00
        + tokens["cached"] * 0.10
        + tokens["cache_write"] * 2.50
        + tokens["output"] * 10.00
    ) / 1_000_000
    web_cost = trace_summary["web_calls"] * 10.00 / 1_000
    total_cost = token_cost + web_cost
    prediction_counts = Counter(frame.classification)
    abstentions = int(frame.classification.isin(ABSTAIN).sum())

    summary = {
        "status": "population_distribution_estimated",
        "population_n": N_POPULATION,
        "sample_n": 382,
        "sample_repositories": int(frame.repo_name.nunique()),
        "confidence_level": 0.95,
        "maximum_design_margin_of_error": 0.05002305824660837,
        "weighted_distribution": {
            row.classification: {
                "sample_count": int(row.sample_count),
                "proportion": float(row.weighted_population_proportion),
                "wilson_95": [float(row.weighted_wilson_95_low), float(row.weighted_wilson_95_high)],
            }
            for row in dist.itertuples()
        },
        "interpretive_groups": {
            row.group: {
                "sample_count": int(row.sample_count),
                "proportion": float(row.weighted_frame_share),
                "design_normal_95": [float(row.normal_95_low), float(row.normal_95_high)],
            }
            for row in groups.itertuples()
        },
        "abstentions": abstentions,
        "classifiable_n": int(len(classifiable)),
        "prior_development_overlap_n": int(frame.prior_development_overlap.sum()),
        "trace_audit": trace_summary,
        "usage": tokens,
        "estimated_api_cost_usd": total_cost,
        "execution_elapsed_seconds": elapsed_seconds,
        "retry_note": "P0123 first returned malformed JSON; no result was retained and the case was rerun once unchanged.",
        "pricing_basis": {
            "as_of": "2026-11-05",
            "model": "gpt-6.1-sol",
            "uncached_input_per_million_usd": 2.00,
            "cached_input_per_million_usd": 0.10,
            "cache_write_per_million_usd": 2.50,
            "output_per_million_usd": 10.00,
            "web_search_per_1000_calls_usd": 10.00,
        },
    }

    frame.sort_values("subsample_id").to_csv(RESULTS / "classified_sample_382.csv", index=False)
    predictions.sort_values("sample_id").to_csv(RESULTS / "predictions.csv", index=False)
    dist.to_csv(RESULTS / "weighted_class_distribution.csv", index=False)
    groups.to_csv(RESULTS / "interpretive_group_distribution.csv", index=False)
    class_contrasts.to_csv(RESULTS / "exploratory_class_contrasts.csv", index=False)
    status_contrasts.to_csv(RESULTS / "exploratory_status_contrasts.csv", index=False)
    by_stratum.to_csv(RESULTS / "distribution_by_task_status.csv", index=False)
    conditional.to_csv(RESULTS / "conditional_distribution_classifiable.csv", index=False)
    sensitivity_dist.to_csv(RESULTS / "sensitivity_excluding_prior_development_overlap.csv", index=False)
    trace_frame.to_csv(RESULTS / "trace_audit.csv", index=False)
    (RESULTS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "EXECUTION_NOTES.md").write_text(
        "# Execution notes\n\n"
        "- The first launch used the system interpreter and failed before any API request.\n"
        "- P0123's first API response was malformed JSON and was not appended. It was rerun once with the identical frozen configuration.\n"
        "- The result set contains exactly one valid prediction for each of the 382 frozen sample units.\n"
        "- No prompt, tool, taxonomy, or sample change occurred after prediction began.\n",
        encoding="utf-8",
    )

    lines = [
        "# LLM-assigned distribution from the 382-case probability sample",
        "",
        f"- Population: {N_POPULATION:,} absent references",
        "- Probability sample: 382 references across 296 repositories",
        "- Design: 130 open-task and 252 completed-task references",
        "- Confidence level: 95%; maximum design margin approximately 5 percentage points",
        f"- Classifiable cases: {len(classifiable)}; abstentions/invalid: {abstentions}",
        f"- Complete auditable traces: {trace_summary['complete_traces']}/382; label leakage: {trace_summary['traces_with_label_leakage']}",
        f"- Execution time: {elapsed_seconds / 60:.1f} minutes",
        f"- Estimated API cost: USD {total_cost:.2f}",
        "",
        "## Weighted distribution",
        "",
        "| LLM-assigned class | n | Weighted frame share | Approximate 95% sampling interval |",
        "|---|---:|---:|---:|",
    ]
    for row in dist.itertuples():
        lines.append(
            f"| `{row.classification}` | {row.sample_count} | {row.weighted_population_proportion:.1%} | "
            f"{row.weighted_wilson_95_low:.1%}–{row.weighted_wilson_95_high:.1%} |"
        )
    lines += [
        "",
        "## Exploratory distribution analysis",
        "",
        "Expected lifecycle change (creation or move/deletion) accounts for 52.9% of weighted model labels (exploratory design-based 95% interval 47.9–57.9); a strict majority is not established even for model labels. Scope or non-file interpretations account for 27.2%, and inaccessible or ambiguous records for 13.1%. Confirmed existence after resolution and problematic absence each account for 3.4%. These groups form a partition of the full frame and keep inaccessible cases in the denominator.",
        "",
        "Planned creation exceeds both non-file references and move/deletion by about 15.5 percentage points in model-assigned frame shares. Their exploratory design-based difference intervals are 8.5–22.5 and 8.8–22.7 percentage points, respectively. Non-file and move/deletion differ by only 0.3 points (interval −5.9 to 6.4), so sampling does not resolve their order.",
        "",
        "Among open tasks, the judge assigns expected creation to 49.2%, versus 26.6% among completed tasks: an open-minus-completed difference of 22.6 points (exploratory design-based interval 12.5–32.8). It assigns move/deletion to 11.5% versus 22.2%, respectively (difference −10.7 points; interval −18.2 to −3.2). These are cross-sectional contrasts of model labels, not observed transitions or causal effects. The intervals exclude model-label error and are not adjusted for multiple comparisons.",
    ]
    lines += [
        "",
        "## Interpretation",
        "",
        "The estimates describe the distribution of model-assigned classes among the 51,979 mechanically absent references, not independently verified human interpretations. The study is not powered for detailed inference within rare classes. Inaccessible/invalid records remain in the main denominator; the classifiable-only distribution is conditional. Wilson intervals use the effective sample size and approximate reference-level sampling uncertainty only. They exclude LLM measurement error and frame error; the five-percentage-point worst-case margin applies to an overall proportion near 0.5, not simultaneously to all classes.",
        "",
        "The judge attempted to read the reference-commit task artifact in every case: 348 found, 32 unavailable commits, and 2 not found at the commit. The frozen Gold contains only three problematic cases and does not support a reliable class-specific sensitivity estimate.",
        "",
        "Two probabilistically retained cases overlap prior development data; a sensitivity table excluding them is provided. Rare-class subgroup analysis, independent population measurement auditing, and narrower-margin replication remain future work and threats to validity.",
    ]
    (RESULTS / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
