# SpecPath: interpreting absent OpenSpec paths

This repository contains the MSR 2027 Mining Challenge study of a single
question: **when a path cited in an OpenSpec task is absent at its reference
commit, what can that absence supportably mean?** It uses the July 2026
SpecMine release and its 51,979 mechanically absent task-to-code references.
The unit is a reference, not a repository or a task.

## Current results

- Human Gold: 90 references from 90 repositories. R1 and R2 initially agreed
  on 83/90 (Cohen's kappa 0.8935); seven disagreements received human
  consensus. The resulting Gold was frozen before the LLM comparison.
  This frozen Gold is the only human reference set used in the study. A later,
  model-informed reconsideration of three cases is excluded.
- LLM judge: GPT-6.1 Sol with the ordered decision tree, exact-commit repository
  tools, and GitHub search for discovery. Its label-blind run agrees with the
  frozen Gold on 82/90 (kappa 0.8782), including 52/60 originally absent
  cases. The decision rule was fixed before evaluating these responses. This
  is observed agreement with the frozen human benchmark; Silver-label error
  in the population sample was not independently measured.
  The judge matched one of three problematic Gold cases and assigned the other
  two to move/deletion; support is too small for reliable sensitivity inference.
- Population Silver: 382 directly judged references, selected by pre-evidence
  random rank within open/completed task strata. No class quotas or tabular
  extrapolation were used.
- Weighted model-assigned estimates: expected creation 34.3%, expected move/removal 18.6%,
  non-file 18.8%, external repository 8.4%, inaccessible/invalid 13.1%,
  confirmed problematic absence 3.4%, and confirmed existence after path
  resolution 3.4%. Approximate sampling intervals and counts are in the
  `results/population_382_agentic/REPORT.md`.
- Distribution analysis: expected lifecycle change accounts for 52.9% of
  weighted model labels, and scope or non-file references for 27.2%. Creation
  is the most frequent model label; non-file and move/removal have similar
  shares. Open-task references receive creation labels more often than
  completed-task references (49.2% versus 26.6%). The comparisons are
  exploratory and describe model labels, not human-confirmed prevalence or
  task transitions.

The approximately five-percentage-point design margin concerns the overall
proportion under reference-level sampling. It does not include model
measurement error or frame error, and it does not support repository-level
inference. There are only 13 Silver cases classified as problematic; this class cannot
support a reliable performance or subgroup claim.

## Manuscript and replication

- `paper/main.tex` and `paper/README.md`
- `validation/ACTIVE_STUDY_PROTOCOL.md`
- `validation/REPRODUCE_FINAL_STUDY.md`
- `paper/figures/decision_flow_compact.png`,
  `paper/figures/decision_flow_compact.svg`, and
  `validation/LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md`
- `validation/PROTOCOL_RECORD_AMENDMENT.json`
- `data/specpath_gold_human_90.csv` and
  `data/specpath_gold_human_90_manifest.json`
- `validation/DECISION_TREE_CASE_EXAMPLES.md`
- `data/population_sample_382/`
- `results/population_382_agentic/`
- `src/verify_population_sample_382.py`,
  `src/run_openai_sol_population_382_agentic.py`, and
  `src/analyze_population_382_agentic.py`, and
  `src/analyze_gold_comparison.py`

This working tree retains the final LLM-judge measurement run and the
probability-sample analysis. Historical technical filenames preserve run
checksums and do not name a separate model in this study.

The public checkout redacts incidental email addresses and user-home paths
from case text and traces. The packaged `RELEASE_REDACTIONS.json` maps the internal
file hashes to the released hashes. Labels, case identifiers, design weights,
and numerical results are unchanged. The analysis below was rerun from this
redacted checkout. Reviewers should access this package through its anonymous
mirror rather than the author's source repository.

Anonymous review link: https://anonymous.4open.science/r/specpath-msr2027-review-artifact-5668/

## Reproducing the analysis

From the repository root, use Python 3.12+ with dependencies in pyproject.toml
and the frozen uv.lock. Recreate the disposable local environment and run:

    uv sync --frozen
    uv run --frozen python src/verify_population_sample_382.py
    uv run --frozen python src/analyze_population_382_agentic.py

The first command checks the released sample's integrity, ranks, and weights;
it does not redraw the sample from the upstream SpecMine frame. The second
regenerates the analysis tables from the frozen sample, model predictions,
and case traces. Re-running the judge is a separate API operation with a
credential and an exact-commit repository cache; the original 90-case input,
prompt, protocol, scripts, and hashes are in the replication package. The
upstream SpecMine raw tables and git caches are not needed to regenerate the
published summary from the included predictions and traces. Exact model
outputs are not guaranteed on a rerun of a stochastic external service.

An optional local .env.local credential file is never part of this package;
the disposable .venv is recreated by uv. For anonymous review, use the
curated, direct-identifier-redacted archive in `dist/`. Its
`RELEASE_REDACTIONS.json` maps original frozen hashes to released member hashes.
