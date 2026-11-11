# LLM-assigned distribution from the 382-case probability sample

- Population: 51,979 absent references
- Probability sample: 382 references across 296 repositories
- Design: 130 open-task and 252 completed-task references
- Confidence level: 95%; maximum design margin approximately 5 percentage points
- Classifiable cases: 332; abstentions/invalid: 50
- Complete auditable traces: 382/382; label leakage: 0
- Execution time: 198.4 minutes
- Estimated API cost: USD 5.29

## Weighted distribution

| LLM-assigned class | n | Weighted frame share | Approximate 95% sampling interval |
|---|---:|---:|---:|
| `confirmed_exists` | 13 | 3.4% | 2.0%–5.7% |
| `confirmed_missing_problematic` | 13 | 3.4% | 2.0%–5.7% |
| `expected_absence_create` | 131 | 34.3% | 29.7%–39.2% |
| `expected_absence_move_or_delete` | 71 | 18.6% | 15.0%–22.8% |
| `external_repository_reference` | 32 | 8.4% | 6.0%–11.6% |
| `non_file_reference` | 72 | 18.8% | 15.2%–23.1% |
| `ambiguous_reference` | 0 | 0.0% | 0.0%–1.0% |
| `inaccessible_or_invalid` | 50 | 13.1% | 10.1%–16.8% |

## Exploratory distribution analysis

Expected lifecycle change (creation or move/deletion) accounts for 52.9% of weighted model labels (exploratory design-based 95% interval 47.9–57.9); a strict majority is not established even for model labels. Scope or non-file interpretations account for 27.2%, and inaccessible or ambiguous records for 13.1%. Confirmed existence after resolution and problematic absence each account for 3.4%. These groups form a partition of the full frame and keep inaccessible cases in the denominator.

Planned creation exceeds both non-file references and move/deletion by about 15.5 percentage points in model-assigned frame shares. Their exploratory design-based difference intervals are 8.5–22.5 and 8.8–22.7 percentage points, respectively. Non-file and move/deletion differ by only 0.3 points (interval −5.9 to 6.4), so sampling does not resolve their order.

Among open tasks, the judge assigns expected creation to 49.2%, versus 26.6% among completed tasks: an open-minus-completed difference of 22.6 points (exploratory design-based interval 12.5–32.8). It assigns move/deletion to 11.5% versus 22.2%, respectively (difference −10.7 points; interval −18.2 to −3.2). These are cross-sectional contrasts of model labels, not observed transitions or causal effects. The intervals exclude model-label error and are not adjusted for multiple comparisons.

## Interpretation

The estimates describe the distribution of model-assigned classes among the 51,979 mechanically absent references, not independently verified human interpretations. The study is not powered for detailed inference within rare classes. Inaccessible/invalid records remain in the main denominator; the classifiable-only distribution is conditional. Wilson intervals use the effective sample size and approximate reference-level sampling uncertainty only. They exclude LLM measurement error and frame error; the five-percentage-point worst-case margin applies to an overall proportion near 0.5, not simultaneously to all classes.

The judge attempted to read the reference-commit task artifact in every case: 348 found, 32 unavailable commits, and 2 not found at the commit. The frozen Gold contains only three problematic cases and does not support a reliable class-specific sensitivity estimate.

Two probabilistically retained cases overlap prior development data; a sensitivity table excluding them is provided. Rare-class subgroup analysis, independent population measurement auditing, and narrower-margin replication remain future work and threats to validity.
