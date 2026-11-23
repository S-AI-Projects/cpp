# R20-T047 Verification & C++ Guidance (`exercises/practice/trinary`)

## What Is Verified

1. **Reference Test Execution (`9/9` Pass)**:
   - Builds `exercises/practice/trinary/.meta/example.cpp` + `.meta/example.h` in an isolated temp directory with `-DEXERCISM_RUN_ALL_TESTS=ON`, verifying all `9` Catch2 cases (including `"_1_yields_decimal_1"`, `"_2_yields_decimal_2"`, and `"_10_yields_decimal_3"`).
2. **Executable `hints.md` Micro-Example & Pitfall**:
   - Extracts the ` ```cpp ` block and ` ```text ` output directly from `exercises/practice/trinary/.docs/hints.md`, compiles under `-std=c++17 -Wall -Wextra -Wpedantic -Werror`, runs it, and verifies exact stdout equality (`zero_copy_same_addr=1` for `std::string const&`, `numeric=1` vs `pitfall_without_minus_zero=49`, and `std::numeric_limits<int>::max()` overflow pre-check).
3. **Negative Controls**:
   - Replacing `digit - '0'` with `digit` fails `"_1_yields_decimal_1"`, unmatched filter (`ZERO-TEST GUARD`), and synthetic child failures.

## How to Run

```bash
python3 work/R20-T047/check.py
```

## Last Result

```text
RESULT: PASS - executed 9 cases
```

## Evidence Index

- [`check.py`](./check.py) — Reference test runner, `hints.md` block compiler/verifier, and negative controls.
- [`notes.md`](./notes.md) — Construct inspection and Issue #48 typo notes.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified reports.
- [`micro-example.log`](./micro-example.log), [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
