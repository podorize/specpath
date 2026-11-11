# Execution notes

- The first launch used the system interpreter and failed before any API request.
- P0123's first API response was malformed JSON and was not appended. It was rerun once with the identical frozen configuration.
- The result set contains exactly one valid prediction for each of the 382 frozen sample units.
- No prompt, tool, taxonomy, or sample change occurred after prediction began.
