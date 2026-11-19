# word-count approach comparison notes

This document compares the reference technique in `exercises/practice/word-count/.meta/example.cpp` with an independent direct scanning alternative.

## Approach Comparison

| Aspect | Reference Implementation | Alternative Implementation |
| --- | --- | --- |
| Architecture | Multi-stage pipeline (`normalize_text` $\to$ `split` $\to$ `trim_word` $\to$ `map`) | Direct single-pass character/index scanner |
| Memory Allocations | Multiple intermediate strings (`normalized`, word vector, trimmed copies) | Minimal; zero intermediate string buffers, direct token construction into map |
| Contraction Handling | Post-split trimming of leading/trailing quotes from each candidate token | In-line lookahead: accepts `'` only if flanked by alphanumeric characters |
| Control Flow | Composition of STL algorithms (`std::transform`, `std::advance`, `std::equal`) | While-loop with state tracking `start` and `current` indices |
| Readability | Clear separation of concerns per stage | Compact, single function, zero allocation overhead |

## Test Verification

Both implementations pass all 14 Catch2 test cases enabled under `EXERCISM_RUN_ALL_TESTS`, including:
- Basic counting (`count one word`, `multiple occurrences of a word`)
- Delimiter variations (`handles cramped lists`, `handles expanded lists`, `ignore punctuation`)
- Contractions and quotation marks (`with apostrophes`, `with quotations`, `quotation for word with apostrophe`)

The comparison check is located in `work/R20-T026/check.py`, and the full alternative source is preserved in `work/R20-T026/alternative.cpp`.
