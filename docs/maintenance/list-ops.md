# List Ops Exercise Maintenance

This document provides maintenance notes and test generation mapping for `exercises/practice/list-ops/`.

## Test Generation Route

**This exercise does NOT use a code generator.**

- **Tests are maintained by hand**: `exercises/practice/list-ops/list_ops_test.cpp` is a hand-written, maintained test file.
- **Canonical cases source**: `exercises/practice/list-ops/.meta/tests.toml` is also maintained by hand.
- **No Jinja template**: No per-exercise template exists in the track generator.
- **No configlet sync**: The `tests.toml` is not generated from canonical problem specifications.

## Generation Command

Since tests are hand-maintained, there is no regeneration command. The "reproducible path" is:
```
tests.toml (source of truth) → list_ops_test.cpp (hand-written to match)
```

## Case-to-Output Mapping for Key Append Cases

| UUID | Description | Test Name in list_ops_test.cpp |
|---|---|---|
| `485b9452-bf94-40f7-a3db-c3cf4850066a` | append entries to a list and return the new list -> empty lists | `append: empty lists` |
| `2c894696-b609-4569-b149-8672134d340a` | append entries to a list and return the new list -> list to empty list | `append: list to empty list` |
| `e842efed-3bf6-4295-b371-4d67a4fdf19c` | append entries to a list and return the new list -> empty list to list | `append: empty list to list` |

These three cases map directly to the first three `TEST_CASE` blocks in `list_ops_test.cpp` (lines 7-42).

## Verification

Run the automated check:
```bash
python3 work/R20-T032/check.py
```

The check:
1. Copies the exercise to a temporary directory
2. Substitutes the reference implementation (example.cpp/.h)
3. Builds with `cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON`
4. Runs the test executable and verifies all 22 tests pass
5. Specifically verifies the three append cases are included and passing