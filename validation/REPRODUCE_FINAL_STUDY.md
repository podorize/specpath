# Reproducing the frozen study

## Published numerical results

The 90-case agreement uses only `data/final/specpath_gold_human_90.csv`, which
was frozen before the reported LLM comparison. The population analysis uses
the frozen 382-case probability sample and its 382 model predictions. Later
model-informed human reconsiderations are excluded from this study.

With Python 3.12+, `uv`, and the frozen `uv.lock`, run from the repository root:

```sh
uv sync --frozen
uv run --frozen python src/verify_population_sample_382.py
uv run --frozen python src/analyze_population_382_agentic.py
```

The verifier checks the released sample's integrity, stratum ranks, and design
weights; it does not redraw the sample from the upstream SpecMine frame. The
analysis regenerates the class distribution, interpretive groups, exploratory
contrasts, overlap sensitivity table, trace audit, and `summary.json` under
`results/population_382_agentic/`. It reads the included predictions and
case-level traces; no API key or repository clone is needed. The 90-case
comparison results and per-class tables are preserved under
`results/validation/openai_sol_90_agentic_v2/` with the exact Gold CSV hash in
its report.

## Frozen judge inputs

The original 90-case runner, its wrapper, source CSV, prompt, and schema
remain frozen in the internal study record. The execution protocol's prose
was amended to reflect the author-confirmed chronology. Its original and
current hashes, and the narrow scope of the amendment, are recorded in
`validation/PROTOCOL_RECORD_AMENDMENT.json`. The publication packager verifies
all other frozen inputs against
`outputs/openai_sol_90_agentic_v2/frozen_manifest.json` and verifies this
specific amendment before creating the anonymous archive. The protocol text
was not supplied to the model; the prompt, predictions, and traces were not
modified. The input CSV contains reviewer-related columns for
provenance, but `src/run_openai_sol_90_agentic.py::load_cases()` passes only
the eleven allowlisted case fields to the model. The released case-start
traces permit checking that no human label or reviewer note was passed.

The population run has its own frozen manifest at
`outputs/openai_sol_population_382_agentic/frozen_manifest.json`. The
manifest records a release-only amendment to the cache path and sample-
description prose, with the original file hashes retained. The case inputs,
prompt, predictions, and traces did not change. Later clarifications about
the analysis are in `validation/ACTIVE_STUDY_PROTOCOL.md` and the analysis
code; they did not change the model calls already made.

## Privacy-safe review archive

The anonymous archive applies the deterministic rules in
`src/redact_public_release.py` to incidental email-like strings and user-home
path segments in text files. `RELEASE_REDACTIONS.json` inside the archive
records each changed member's original and released SHA-256 hashes and the
number of substitutions. The run records preserve original hashes for
release-amended files; original hashes also intentionally differ from public
members that were redacted. Case identifiers, commit SHAs,
classes, weights, and numerical results are unchanged. Re-running
`src/analyze_population_382_agentic.py` from the public archive reproduces
the published distribution and audits without an API key.

The archive packager runs in the internal workspace, where the original frozen
90-case input and traces are available. Those unredacted inputs are not added
to a public checkout merely to rebuild the ZIP; the release archive contains
their redacted counterparts and the hash mapping.

## Re-executing model calls

A new execution requires access to GPT-6.1 Sol through the Responses API and
local, read-only Git caches containing the cited repositories at their exact
reference commits. The 90-case runner expects one bare Git repository per
case at `outputs/openai_sol_90_v3/git_cache/F001` through `F090`; the
repository names and commit SHAs are in the included source CSV. The
382-case runner expects bare Git repositories under the cache path configured
in `src/run_openai_sol_population_382_agentic.py`, keyed by repository name.
The original caches are omitted from this
anonymous archive because they contain unrelated Git history and may include
personal metadata. The included traces preserve the substantive tool outputs
used in the published decisions, with incidental direct identifiers redacted.

After reconstructing a cache, verify the 90-case inputs and exact-commit
availability without API calls:

```sh
python src/run_openai_sol_90_agentic_v2.py --dry-run
```

To make new API calls, choose a **new** output directory and provide a
credential through the environment. Model outputs need not be byte-identical
because the hosted model and web discovery can vary. The published
predictions and traces, rather than a fresh run, are the auditable record of
the reported estimates.
