# R20-T050 Verification & Contract Decision Table (`exercises/practice/darts`)

## What Is Verified

1. **Reference Test Execution (`13/13` Pass)**:
   - Builds `exercises/practice/darts/.meta/example.cpp` + `.meta/example.h` in an isolated temp directory with `-DEXERCISM_RUN_ALL_TESTS=ON`, passing all `13` Catch2 cases (including `"missed_target"`, `"on_the_outer_circle"`, and `"on_the_middle_circle"`).
2. **Decision Table & Scratch Reproduction (`hints.md` <-> `darts_test.cpp`)**:
   - Parses the decision table in `exercises/practice/darts/.docs/hints.md` and the `REQUIRE` assertions in `exercises/practice/darts/darts_test.cpp`, verifies exact input and outcome agreement, and compiles/runs a standalone scratch C++ harness against `.meta/example.cpp` (`(-9, 9) -> 0`, `(0, 10) -> 1`, `(-5, 0) -> 5`).
   - Documents `Unspecified behaviour` without imposing extra exception, coercion, or ordering requirements.
3. **Negative Controls**:
   - Assertion failure on `"missed_target"`, unmatched filter (`ZERO-TEST GUARD`), and synthetic child failures.

## How to Run

```bash
python3 work/R20-T050/check.py
```

## Last Result

```text
RESULT: PASS - executed 13 cases
```

## Evidence Index

- [`check.py`](./check.py) — Reference test runner, decision-table/test cross-checker, scratch repro, and negative controls.
- [`notes.md`](./notes.md) — Contract inspection notes.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified reports.
- [`scratch-repro.log`](./scratch-repro.log), [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
