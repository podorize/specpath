# LLM-judge comparison against the frozen human Gold

The LLM judge returned one valid structured classification for each of the 90
human-reviewed cases. The predictions were made without human labels, notes,
or the mechanical anchor-existence flag in their inputs.

| Scope | Agreement | Cohen's kappa | Supported-class macro-F1 |
| --- | ---: | ---: | ---: |
| All 90 | 86/90 (95.6%) | 0.9398 | 0.8906 |
| Original anchor-absent 60 | 56/60 (93.3%) | 0.9033 | 0.8724 |

R1 and R2 initially agreed on 83/90. Their seven initial disagreements
received human consensus, and five methodological Gold corrections were
confirmed before this LLM-judge comparison. The Gold version used here is
data/final/specpath_gold_human_90.csv (SHA-256
901baec28fc6c504b1216f5fb3ef7f09d4c211a351ffb26abf957c4dfc35214a).
It contains three problematic cases. The four exact disagreements are F025,
F033, F049, and F069.

All 90 case traces are complete; no prohibited label fields were found in
starting records. The task artifact was read or attempted in all 90 cases.
The agent made 270 repository tool calls and no GitHub web calls in this run,
although web search was available.

The frozen Gold had three problematic cases in the originally absent subset.
The judge matched one and assigned the other two to expected move or deletion;
this observed 1/3 recall is too small for reliable rare-class sensitivity
inference. A later, model-informed
human reconsideration of three cases is excluded from this study and package.
The decision rule was fixed before evaluating the reported responses. The
86/90 is label-blind, observed agreement with the frozen human benchmark;
classification error in the population Silver was not independently measured.
