# R20-T046 Verification & Approach Comparison (`exercises/practice/alphametics`)

## What Is Verified

1. **Two Distinct Implementations (`10/10` Cases Pass Both)**:
   - **Reference (`.meta/example.cpp`):** Place-value `weight` vector per letter (`<= 10`) + letter-by-letter DFS checking `sum == 0` at leaf `pos == n`.
   - **Alternative (`work/R20-T046/alternative.cpp` + `.h`):** `ColumnCarrySolver` aligning addends and result right-to-left by decimal column, enforcing `col_sum % 10 == result_digit`, deducing unassigned result digits in `O(1)`, and forwarding `carry = col_sum / 10`.
   - Normalized token-stream similarity (`SequenceMatcher`) is below `0.70`, proving `alternative.cpp` is not a renamed copy.
   - Instrumented node comparison measures recursion nodes visited across both algorithms (`counts.json`).
2. **Guidance (`exercises/practice/alphametics/.docs/hints.md`)**:
   - Compares both representations, documents trade-offs, and traces `"I + BB == ILL"` step-by-step without publishing a full solution listing.
3. **Negative Controls**:
   - Mutating `"I + BB == ILL"`, zero-test filter (`ZERO-TEST GUARD`), and non-zero child exit codes.

## How to Run

```bash
python3 work/R20-T046/check.py
```

## Last Result

```text
RESULT: PASS - executed 10 cases
```

## Evidence Index

- [`check.py`](./check.py) — Dual-implementation runner, token similarity check, search-node counter, and negative controls.
- [`alternative.cpp`](./alternative.cpp) & [`alternative.h`](./alternative.h) — Independent column-by-column carry solver.
- [`notes.md`](./notes.md) — Spec and implementation comparison notes.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`alternative-results.xml`](./alternative-results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified reports.
- [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`alternative-build.log`](./alternative-build.log), [`alternative-run.log`](./alternative-run.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
