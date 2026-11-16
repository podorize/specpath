"""Recompute the frozen 90-case Gold comparison without rerunning the model."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/specpath_gold_human_90.csv"
RESULTS = ROOT / "results/validation/openai_sol_90_agentic_v2"


def metrics(rows: list[dict[str, str]]) -> tuple[dict, list[str], list[list[int]]]:
    labels = sorted({r["gold_human_classification"] for r in rows} | {r["agentic_classification"] for r in rows})
    n = len(rows)
    matches = sum(r["gold_human_classification"] == r["agentic_classification"] for r in rows)
    gold = Counter(r["gold_human_classification"] for r in rows)
    pred = Counter(r["agentic_classification"] for r in rows)
    expected = sum(gold[l] * pred[l] for l in labels) / (n * n)
    observed = matches / n
    kappa = (observed - expected) / (1 - expected)
    per_class = []
    matrix = []
    for g in labels:
        row = []
        for p in labels:
            row.append(sum(r["gold_human_classification"] == g and r["agentic_classification"] == p for r in rows))
        matrix.append(row)
        tp = row[labels.index(g)]
        fp = sum(r["gold_human_classification"] != g and r["agentic_classification"] == g for r in rows)
        fn = sum(r["gold_human_classification"] == g and r["agentic_classification"] != g for r in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({"category": g, "support": gold[g], "predicted": pred[g], "true_positive": tp,
                          "precision": precision, "recall": recall, "f1": f1})
    supported = [x["f1"] for x in per_class if x["support"]]
    return {"n": n, "matches": matches, "accuracy": observed, "cohen_kappa": kappa,
            "macro_f1_gold_supported_classes": sum(supported) / len(supported),
            "gold_supported_class_count": len(supported), "per_class": per_class}, labels, matrix


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    gold = {r["review_id"]: r for r in csv.DictReader(GOLD.open())}
    case_path = RESULTS / "case_comparison.csv"
    rows = list(csv.DictReader(case_path.open()))
    for row in rows:
        for field in gold[row["review_id"]]:
            if field in row:
                row[field] = gold[row["review_id"]][field]
        row["agentic_matches_gold"] = str(row["gold_human_classification"] == row["agentic_classification"])
        row["decision_matches_gold"] = str(row["gold_human_classification"] == row["agentic_classification"])
        row["gold_decision"] = row["gold_human_classification"]
    write_csv(case_path, list(rows[0]), rows)

    all_metrics, labels, matrix = metrics(rows)
    missing = [r for r in rows if r["validation_group"] == "completed + missing" or r["validation_group"] == "open + missing"]
    missing_metrics, _, _ = metrics(missing)
    per_class = all_metrics.pop("per_class")
    write_csv(RESULTS / "per_class_all_90.csv", list(per_class[0]), per_class)
    with (RESULTS / "confusion_all_90.csv").open("w", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["Gold", *labels])
        for label, values in zip(labels, matrix): writer.writerow([label, *values])
    disagreements = [r for r in rows if r["gold_human_classification"] != r["agentic_classification"]]
    write_csv(RESULTS / "disagreements.csv", list(disagreements[0]), disagreements)
    summary = json.loads((RESULTS / "summary.json").read_text())
    summary["all_90"] = all_metrics
    summary["missing_60"] = missing_metrics
    summary["gold_distribution"] = dict(Counter(r["gold_human_classification"] for r in rows))
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    report = f"""# LLM-judge comparison against the consensus-only human Gold

| Scope | Agreement | Cohen's kappa | Supported-class macro-F1 |
| --- | ---: | ---: | ---: |
| All 90 | {all_metrics['matches']}/90 ({all_metrics['accuracy']:.1%}) | {all_metrics['cohen_kappa']:.4f} | {all_metrics['macro_f1_gold_supported_classes']:.4f} |
| Original anchor-absent 60 | {missing_metrics['matches']}/60 ({missing_metrics['accuracy']:.1%}) | {missing_metrics['cohen_kappa']:.4f} | {missing_metrics['macro_f1_gold_supported_classes']:.4f} |

R1 and R2 initially agreed on 83/90 labels. The seven initial disagreements were resolved by human consensus, and that consensus-only Gold was frozen before the LLM comparison. The LLM responses were not rerun. The comparison is label-blind observed agreement with the frozen human benchmark; it does not measure Silver-label error in the population sample.

The frozen Gold contains three problematic cases. The judge matched one and missed two; this 1/3 observed recall is too small for reliable rare-class sensitivity inference.
"""
    (RESULTS / "REPORT.md").write_text(report)
    print(json.dumps({"all_90": all_metrics, "missing_60": missing_metrics, "disagreements": len(disagreements)}, indent=2))


if __name__ == "__main__":
    main()
