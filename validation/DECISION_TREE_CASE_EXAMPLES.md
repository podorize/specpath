# Decision-tree case examples

These examples explain the ordered rules. They are drawn from the 90 human-reviewed
cases, so they are illustrations of the measurement instrument, not independent
validation or prevalence evidence. Source repository, commit, task URL, reviewer
notes, and full task context are in `data/final/specpath_gold_human_90.csv`.

| Case | Commit-aligned observation | Decisive tree test | Human conclusion |
| --- | --- | --- | --- |
| F001 | The task requests a new `apps/server/src/db/__tests__/0010_summary_length_check.test.ts`; that file is absent at the reference commit. | After validating a file reference and absence, step 4 reads an instruction to add a new test. | `expected_absence_create` |
| F061 | The task requests rewriting `python/scripts/test_cl_buck.py` and uses its existing implementation as a comparison point, but the file is absent at the reference commit. | Step 4 finds an assumed existing dependency, not an instruction to create it. | `confirmed_missing_problematic` |

F001 and F061 show why the same mechanical entry condition cannot itself imply a
defect. The examples are illustrations from the frozen Gold; they do not
estimate class prevalence or LLM performance on new cases.

The complete decision sequence and output taxonomy are in
`validation/ACTIVE_STUDY_PROTOCOL.md` and the judge prompt; the frozen Gold CSV
preserves the human decisions used for the reported comparison.
