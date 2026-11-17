# LLM-judge comparison against the consensus-only human Gold

| Scope | Agreement | Cohen's kappa | Supported-class macro-F1 |
| --- | ---: | ---: | ---: |
| All 90 | 82/90 (91.1%) | 0.8782 | 0.8093 |
| Original anchor-absent 60 | 52/60 (86.7%) | 0.8006 | 0.7689 |

R1 and R2 initially agreed on 83/90 labels. The seven initial disagreements were resolved by human consensus, and that consensus-only Gold was frozen before the LLM comparison. The LLM responses were not rerun. The comparison is label-blind observed agreement with the frozen human benchmark; it does not measure Silver-label error in the population sample.

The frozen Gold contains three problematic cases. The judge matched one and missed two; this 1/3 observed recall is too small for reliable rare-class sensitivity inference.
