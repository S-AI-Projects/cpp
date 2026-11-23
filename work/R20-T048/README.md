# R20-T048 Verification & Metadata Map (`exercises/practice/diamond`)

## What Is Verified

1. **Metadata & Path Validation (`tools/course_checks/r20-t048.py`)**:
   - Parses `exercises/practice/diamond/.meta/config.json` `"files"` directly via JSON, rejects absolute paths / `..` / out-of-tree symlinks (`exit 3`), missing test (`exit 4`), missing reference (`exit 5`), missing solution/editor (`exit 6`), and CMake naming disagreements (`exit 7`).
   - Passes (`exit 0`) on the real `exercises/practice/diamond` metadata (confirming no `"editor"` key is declared and no `.meta/config.json` changes are needed).
   - Fails with distinct error codes and messages on three temp fixtures (`missing_reference` -> `5`, `missing_test` -> `4`, `outside_exercise_path` -> `3`).
2. **Isolated Reference Test Execution (`5/5` Pass)** & **Negative Controls**:
   - All `5` Catch2 cases (including `"Degenerate case with a single 'A' row"`, `"Degenerate case with no row containing 3 distinct groups of spaces"`, and `"Smallest non-degenerate case with odd diamond side length"`) pass under `-DEXERCISM_RUN_ALL_TESTS=ON`, plus assertion failure, zero-test filter (`ZERO-TEST GUARD`), and child exit failure controls.

## How to Run

```bash
python3 tools/course_checks/r20-t048.py exercises/practice/diamond
python3 work/R20-T048/check.py
```

## Last Result

```text
RESULT: PASS - executed 5 cases
```

## Evidence Index

- [`check.py`](./check.py) & [`../../tools/course_checks/r20-t048.py`](../../tools/course_checks/r20-t048.py) — Verification & reusable config/path validator.
- [`notes.md`](./notes.md) & [`../../docs/maintenance/diamond.md`](../../docs/maintenance/diamond.md) — File role map and runner path resolution docs.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified reports.
- [`validator-real.log`](./validator-real.log), [`validator-fixture-missing-ref.log`](./validator-fixture-missing-ref.log), [`validator-fixture-missing-test.log`](./validator-fixture-missing-test.log), [`validator-fixture-outside-path.log`](./validator-fixture-outside-path.log), [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
