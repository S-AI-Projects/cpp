# Hints

## Approach Selection

When implementing `word_count::words`, two primary architectural patterns are commonly considered in C++:

### 1. Multi-Stage Pipeline (Transformation & Splitting)
- **Concept**: Transform the raw string through distinct phases:
  1. Replace non-word punctuation characters with whitespace while preserving apostrophes and converting to lowercase.
  2. Split the normalized string into tokens (`std::vector<std::string>`).
  3. Strip leading and trailing apostrophes from each token (to distinguish quotes from contractions).
  4. Accumulate frequencies in `std::map<std::string, int>`.
- **Trade-off**: Highly modular and easy to read, but incurs memory overhead and allocations for intermediate normalized strings and token vectors.

### 2. Direct Single-Pass Index Scanning
- **Concept**: Walk the input string directly using index pointers (`start`, `end`) without intermediate buffer allocation:
  - Skip non-alphanumeric delimiters.
  - Scan the word token, accepting an apostrophe only if flanked by alphanumeric characters (internal contractions like `"can't"`).
  - Construct and lower-case each discovered token directly into the map.
- **Trade-off**: Minimizes heap allocations and avoids temporary container copies, but requires careful character-level lookahead to handle apostrophe boundaries.

### Worked Example: Handling Quotations vs Contractions

Consider the input:
```
"Joe can't tell between 'large' and large."
```

- In **Approach 1**, the string is normalized to `"joe can't tell between 'large' and large "`, split into tokens where `"'large'"` is trimmed of outer quotes to `"large"`, while `"can't"` retains its internal apostrophe.
- In **Approach 2**, the index scanner skips the quote before `'large'` because it is preceded and followed by non-alphanumeric characters, directly extracting `"large"`, while accepting the apostrophe in `"can't"` because both `'n'` and `'t'` are alphanumeric.

Both approaches yield the exact word counts:
```cpp
{{"and", 1}, {"between", 1}, {"can't", 1}, {"joe", 1}, {"large", 2}, {"tell", 1}}
```
