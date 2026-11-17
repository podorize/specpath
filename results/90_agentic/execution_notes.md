# Execution notes

- The final LLM-judge run produced 90 valid, unique predictions.
- F089's first API response could not be parsed as JSON (`JSONDecodeError` at
  character 567) despite the requested strict schema. No prediction from that
  attempt was appended to the result set.
- F089 was rerun once with the identical frozen model, prompt, tools, schema,
  and case input. The successful structured response is the only F089 result in
  `predictions.jsonl`.
- No case label was edited or remapped after prediction.
