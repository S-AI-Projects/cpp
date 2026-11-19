# Hints

## General

- Pay close attention to punctuation and capitalization in the output string.
- The test suite validates an exact character-by-character match against the target greeting.
- A common mistake is omitting punctuation (such as the comma separating the greeting and target, or the concluding exclamation mark) or altering capitalization (for instance, lowercasing words).
- If your implementation returns greeting text like `"Hello World!"` (missing the comma) or `"Hello, world!"` (lowercase 'w'), the exact string comparison in Catch2 will fail. Ensure every character, including delimiters and casing, strictly matches the specification.
