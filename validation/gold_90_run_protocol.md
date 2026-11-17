# GPT-6.1 Sol agentic review of the human Gold 90

## Status

This protocol describes the complete 90-case run reported in the paper. Its
decision rule was finalized before the reported responses were evaluated.
The human Gold was frozen before the comparison. The judge received no human
labels or reviewer notes while classifying the cases.

## Fixed components

- same 90 label-free starting records supplied to human reviewers;
- same frozen human Gold, hidden during prediction;
- same eight-class taxonomy and ordered human decision tree;
- exact-anchor, read-only repository tools;
- GitHub web search for human-comparable discovery;
- model `gpt-6.1-sol`;
- Responses API, reasoning `standard`/`low`, strict structured output;
- maximum 40 tool calls per API response and 50 per case;
- complete case-level traces and no stored API responses.

## Temporal-validity rule

For a supplied source occurrence that comes from a different snapshot and
cannot be verified in the exact anchor task artifact, the record is temporally
invalid and must be labeled `inaccessible_or_invalid`. `ambiguous_reference`
is reserved for a valid, anchor-aligned record whose semantic class remains
uncertain after reasonable investigation.

## Evaluation status

Report exact agreement, Cohen's kappa, supported-class macro-F1, per-class
results, abstentions, classify/abstain agreement, tool-use audit, and all
disagreements. This benchmark comparison does not directly measure
Silver-label error in the population sample.
