# Agentic classification protocol for the 382-reference population sample

## Objective

Estimate the population distribution of what an absent OpenSpec path permits
one to conclude. The target population contains 51,979 literal path references
recorded as absent at their reference commits.

## Sample

The 382 cases are a proportionally allocated nested probability sample from
the 1,200-case frame: 130 open tasks and 252 completed tasks. Selection uses
only the parent sample's within-stratum random rank, frozen before repository
evidence or semantic labels. No outcome-based complement or replacement is
allowed.

## Measurement architecture

- exact tree-aligned V2 decision prompt used for the final 90-case development
  run;
- model `gpt-6.1-sol`, Responses API, standard mode, low reasoning effort;
- same read-only repository capabilities and GitHub web-search availability;
- all main-repository operations fixed to the reference commit;
- same eight-class taxonomy and ordered decision tree;
- strict structured output and complete case-level traces;
- no human Gold, reviewer note, prior LLM label, access status, or mechanical
  `exists_at_anchor` field in model inputs;
- no prompt or tool changes after population predictions begin.

## Analysis

Estimate weighted class proportions using the known stratum weights and report
95% confidence intervals with finite-population correction. Keep
`inaccessible_or_invalid` and abstentions in the population distribution;
analyses restricted to semantically classifiable records are conditional and
must be labeled as such.

The study is powered for overall distribution (maximum margin approximately
five percentage points), not detailed inference within rare classes. Rare-
class modeling and subgroup analysis are future work and a threat to validity.
