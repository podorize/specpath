# Publication readiness and advisor handoff

## What is ready

The active paper source, frozen 90-case human Gold, probability sample, 382 model
predictions, weighted result tables, decision instrument, and analysis code
are aligned to the current study. The main claim concerns model-assigned
interpretations of mechanically absent paths in the July 2026 SpecMine
release. It does not equate absence with a defect or claim a validated defect
detector.

The internal advisor handoff is:

1. paper/main.tex and output/pdf/specpath_msr2027_anonymous.pdf
   (current anonymous manuscript and three-page local preview);
2. results/population_382_agentic/REPORT.md, weighted_class_distribution.csv,
   interpretive_group_distribution.csv, and the exploratory contrast tables;
3. validation/ACTIVE_STUDY_PROTOCOL.md;
4. paper/figures/final_decision_tree.svg;
5. data/final/specpath_gold_human_90_manifest.json and
   data/final/population_sample_382/specpath_population_sample_382_manifest.json.

## Anonymous artifact allowlist

The curated local candidate is
`dist/specpath_msr2027_anonymous_replication_candidate.zip`. It contains:

- README.md, pyproject.toml, and this guide;
- paper/main.tex, paper/IEEEtran.cls, paper/references.bib, the print-ready
  decision tree, and its editable source;
- validation/ACTIVE_STUDY_PROTOCOL.md,
  validation/REPRODUCE_FINAL_STUDY.md,
  validation/OPENAI_SOL_90_AGENTIC_V2_PROTOCOL.md,
  validation/PROTOCOL_RECORD_AMENDMENT.json,
  validation/OPENAI_SOL_POPULATION_382_AGENTIC_PROTOCOL.md,
  validation/LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md,
  validation/llm_judge_output_schema_openai_agentic.json;
- data/final/specpath_gold_human_90.csv and its provenance manifest;
- data/interim/validation_final_90_en.csv, the exact hashed 90-case runner input;
- validation/DECISION_TREE_CASE_EXAMPLES.md;
- validation/METHODOLOGICAL_REVIEW_7_CASES.md, the completed human methodological review;
- data/final/population_sample_382/ (CSV and manifest; Parquet optional);
- results/validation/openai_sol_90_agentic_v2/;
- results/population_382_agentic/;
- outputs/openai_sol_population_382_agentic/predictions.jsonl,
  frozen_manifest.json, and traces/;
- src/verify_population_sample_382.py,
  src/run_openai_sol_population_382_agentic.py,
  src/run_openai_sol_90_agentic.py,
  src/run_openai_sol_90_agentic_v2.py,
  src/analyze_population_382_agentic.py, and the public-redaction rules.

The local LICENSE contains an author name, so it is omitted from the anonymous
review candidate. This candidate is for review access only; attach the
original license to the public post-review release.

The frozen Gold is the only human reference used for 86/90. Later
model-informed human reconsiderations are excluded from the study and the
anonymous archive, while their occurrence remains disclosed. The analysis and
382-case sample verification run from the listed files. The population run
manifest records the release-only cache-path and protocol-prose amendment,
retaining original hashes; the 90-case protocol amendment is separately
documented. Privacy redaction changes some public
members' bytes, and `RELEASE_REDACTIONS.json` records both hashes. Exact model
re-execution also needs the upstream
SpecMine records or exact-commit Git caches, which are not repackaged because
of unrelated history and possible personal metadata. Included predictions and
traces support auditing without new API calls; a new model run may differ.

Do not publish the unredacted internal working directory. The public GitHub
checkout uses the ZIP's redacted case text and traces, with original and
released hashes in `dist/RELEASE_REDACTIONS.json`. The ignored local .env.local is
retained for optional model reruns; the Python environment can be recreated
from uv.lock. The named license identifies the author. Superseded
analyses and large repository caches have been moved
to a recoverable temporary backup outside the repository. Review traces
for any non-public content before sharing. The archive integrity check passed
for all members, including 382 population and 90 Gold-benchmark case traces.
Its public-redaction step replaced 34 email-like strings and 78 user-home path
occurrences across 31 files; a second scan found none remaining. A literal
API-key and local-author-path scan also found no matches. The released archive
reproduced the weighted distribution from its own redacted files. This
automated check does not detect every possible personal identifier; inspect
less-structured excerpts before hosting.

## Remaining submission gates

- Recompile the IEEE manuscript in the final submission environment. The
  local Tectonic build produced a three-page PDF; all pages were visually
  checked, and the log showed no overfull boxes. Font substitution can vary
  across TeX installations. The local PDF is
  `output/pdf/specpath_msr2027_anonymous.pdf`.
- Ask the authors and advisor to check every claim, human decision chronology,
  ethics wording, and whether the 13 problematic Silver cases justify the
  intended interpretation. In particular, the 86/90 result is benchmark agreement
  and the 3.4% model-assigned share excludes measurement error.
- Complete a final review of less-structured source excerpts, host the anonymous artifact,
  then insert its stable anonymous
  URL into the manuscript. Do not insert a personal GitHub URL or a claim
  that an archive already exists.
- Check PDF author fields, embedded metadata, and archive commit history for
  identity disclosure before submission.
- Submit paper metadata and PDF through the official Challenge site. The
  [official call](https://2027.msrconf.org/track/msr-2027-mining-challenge)
  lists December 18, 2026 for the abstract and December 23, 2026 for the
  paper (AoE); it also requires IEEE formatting, double anonymity, an
  ethical implications section, and the strict 4+1 page limit.

No external archive, Overleaf project, or conference submission was changed
by this repository preparation.
