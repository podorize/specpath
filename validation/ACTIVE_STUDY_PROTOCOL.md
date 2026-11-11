# Active SpecPath study protocol

## Question and frame

When a path cited in an OpenSpec task is absent at the reference commit, what
can that absence supportably mean? The population is the 51,979 SpecMine
literal references marked absent at their anchor commits (4,444 repositories).
One reference is one sampling unit. The July 2026 SpecMine release is the
upstream snapshot.

## Human measurement

The 90-case Gold comprises 30 completed/existing controls, 30
completed/missing, and 30 open/missing references from 90 repositories.
R1/R2 initial agreement was 83/90, kappa 0.8935. Seven cases were resolved
by human consensus. A subsequent methodological review changed five labels.
The frozen Gold CSV and manifest record those decisions. A later human
reconsideration of three cases occurred after model disagreements were known;
its decisions are excluded from this study's Gold, evaluation, and package. Initial
agreement describes the two reviewers' recorded initial decisions; their
blinding chronology was not independently verified.

## Construct

The eight classes and precedence are:

1. Verify occurrence and exact-commit evidence; if invalid or unavailable,
   use inaccessible_or_invalid.
2. Resolve non-file syntax and explicit external-repository scope.
3. Check literal and resolved existence at the anchor commit.
4. For absent files, distinguish explicit creation, move/removal/replacement,
   and assumed pre-existing missing dependencies.
5. Use ambiguous_reference if remaining evidence is insufficient.

The detailed prompt is LLM_JUDGE_PROMPT_FINAL_90_OPENAI_AGENTIC_V2.md. Current
GitHub content can aid discovery but is not evidence of anchor-commit state.

## Model and Gold comparison

The LLM judge uses GPT-6.1 Sol via the Responses API, standard mode,
low reasoning effort, structured output, read-only exact-commit repository
tools, and GitHub web search. Its 90-case label-blind run matched the Gold
frozen before later human reconsideration on 86/90 (kappa 0.9398).
The decision rule was fixed before the responses were evaluated. This is
observed agreement with the frozen human benchmark; it does not directly
measure classification error in the population Silver. The frozen Gold
has three problematic cases; the judge matched one and assigned the other two
to expected move or deletion. This is too little support for reliable
rare-class sensitivity inference. No later, model-informed human decisions
are used in the study.

## Population sample and analysis

The final 382 cases are a nested probability sample from the frozen
1,200-case frame. Within each task-status stratum, the first pre-evidence
random ranks were retained: 130 of 17,752 open and 252 of 34,227 completed.
No label, access result, or class quota affected selection. Each case uses
weight N_h/n_h. Population proportions are weighted by the two stratum
shares. Inaccessible/invalid remains in the primary denominator.

The approximate 95% worst-case finite-population margin is 5.002 percentage
points for an overall proportion around 0.5 under reference-level sampling.
The published class intervals use an effective-sample-size Wilson
approximation. They do not quantify LLM error, frame error, superpopulation
uncertainty, or latent classes within inaccessible cases. The exhaustive
interpretive-group summaries and class/status contrasts are exploratory,
unadjusted comparisons of model labels; their design-based intervals describe
sampling variation only. The frozen 382-case execution protocol records the
pre-run configuration, while this document records later analysis choices.
The two development-overlap units remain in the primary sample and are
excluded only in a sensitivity table.

The frozen sample manifest, model run manifest, 382 predictions, 382 traces,
analysis code, and output tables are the provenance chain. A malformed first
response for P0123 was retried once with the same configuration.

## Scope of inference

The result is an estimate of model-assigned interpretations in the specified
reference frame. It is not a measured rate of code defects, later
implementation, or developer mistakes. Rare-class, repository-level, and
longitudinal analyses require additional designs. No independent human audit
of the 382-case Silver sample is part of the current study. The manuscript
therefore does not claim that Silver-label error has been measured.
