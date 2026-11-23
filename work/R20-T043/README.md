# R20-T043 Verification & Evidence (`exercises/practice/dnd-character`)

## What Is Verified

1. **Maintained Reference Execution (`18/18` Pass)**:
   - Builds `exercises/practice/dnd-character/.meta/example.cpp` + `.meta/example.h` in an isolated temporary directory with `-DEXERCISM_RUN_ALL_TESTS=ON`. All `18` Catch2 test cases pass, including `"ability modifier for score 3 is -4"`, `"ability modifier for score 4 is -3"`, and `"ability modifier for score 5 is -3"`.
2. **Deliberate Mutant Rejection (`work/R20-T043/mutant.cpp`)**:
   - Replaces `std::floor((static_cast<double>(score) - 10) / 2)` with signed integer division `(score - 10) / 2`.
   - Builds in a separate isolated temporary directory cleanly under `-Wall -Wextra -Wpedantic -Werror`, exits non-zero when executed (`rc=4`), and fails exactly the `4` odd scores below `10`: scores `3`, `5`, `7`, and `9` (asserted in `mutant-results.xml`).
   - Direct `3..18` probe verifies the smallest rejecting input in the spec domain is **`score = 3`** (`-4` expected vs `-3` mutant).
3. **Documentation & Hints**:
   - `exercises/practice/dnd-character/.docs/hints.md` explains the floor-rounding contract and integer truncation pitfall using diagnostic `score = 3 -> -4` without exposing a full solution.
   - `docs/maintenance/dnd-character.md` documents the mutant diff, failing UUIDs, `3..18` comparison table, and minimal rejecting input.

## How to Run

```bash
python3 work/R20-T043/check.py
```

## Last Result

```text
RESULT: PASS - executed 18 cases
```

## Evidence Index

- [`check.py`](./check.py) — Isolated build, mutation runner, `3..18` probe, and negative controls.
- [`mutant.cpp`](./mutant.cpp) — Single-expression integer-division mutant of `modifier`.
- [`notes.md`](./notes.md) — Spec, test suite, and mutant trace.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`mutant-results.xml`](./mutant-results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified evidence.
- [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`mutant-run.log`](./mutant-run.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
