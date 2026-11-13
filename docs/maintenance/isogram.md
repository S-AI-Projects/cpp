# Isogram Exercise Maintenance

This document provides maintenance notes and mutation testing records for `exercises/practice/isogram/`.

## Mutation Testing Record

### Mutant: Case-Sensitive Comparison (removed `tolower()`)

**Changed line in reference implementation:**
```cpp
// Original (correct):
auto ret = chars.insert(tolower(ch));

// Mutant (buggy):
auto ret = chars.insert(ch);  // Missing tolower() - case sensitive
```

**Effect:** The mutant treats `A` and `a` as different characters.

**Rejecting Test Cases:**
| UUID | Test Name | Input | Expected | Mutant Result |
|------|-----------|-------|----------|---------------|
| `f1a7f6c7-a42f-4915-91d7-35b2ea11c92e` | word_with_duplicated_character_in_mixed_case | `"Alphabet"` | `false` | `true` ❌ |
| `14a4f3c1-3b47-4695-b645-53d328298942` | word_with_duplicated_character_in_mixed_case_lowercase_first | `"alphAbet"` | `false` | `true` ❌ |

**Smallest diagnostic input:** `"Alphabet"` (7 chars) — contains both uppercase `A` and lowercase `a`.

**Hint added:** See `.docs/hints.md` for the debugging hint explaining the contract.

## Automated Check

Run the check:
```bash
python3 work/R20-T033/check.py
```

The check:
1. Verifies all 14 tests pass with the reference implementation
2. Runs the mutant and confirms the 2 mixed-case tests fail
3. Reports test counts and assertions