# R20-T049 Verification & Isolated Runner (`exercises/practice/bank-account`)

## What Is Verified

1. **Reusable Isolated Runner (`tools/course_checks/r20-t049.py`)**:
   - Supports `--exercise <slug>` (default `bank-account`), `--reference-dir <dir>`, and `--filter <catch-test-spec>`.
   - Protects learner files via SHA-256 hashing before/after in `finally:`, cleans up `r20-t049-*` temp dirs on exit, failure, `KeyboardInterrupt`, and `SIGTERM`, links `Threads::Threads`, enforces the zero-test guard, and prints the real case count.
2. **Four Verified Scenarios (`work/R20-T049/check.py`)**:
   - **Real reference:** exits `0` with `17/17` executed cases (including `"Newly opened account has zero balance"`, `"Single deposit"`, `"Multiple deposits"`, and the 1000-thread concurrency test).
   - **Failing reference (`--reference-dir`):** exits non-zero; temp dir cleaned up; learner hashes unchanged.
   - **Empty selection (`--filter "no-such-test*"`):** Catch2 exits `0`, runner exits non-zero via `ZERO-TEST GUARD`; temp dir cleaned up; learner hashes unchanged.
   - **Interrupted run (`SIGINT` mid-build):** terminates active child process, removes printed temp dir, and leaves learner hashes untouched.

## How to Run

```bash
python3 tools/course_checks/r20-t049.py --exercise bank-account
python3 work/R20-T049/check.py
```

## Last Result

```text
RESULT: PASS - executed 17 cases
```

## Evidence Index

- [`check.py`](./check.py) & [`../../tools/course_checks/r20-t049.py`](../../tools/course_checks/r20-t049.py) — Scenario suite and isolated runner.
- [`notes.md`](./notes.md) & [`../../docs/maintenance/bank-account.md`](../../docs/maintenance/bank-account.md) — Exercise inspection and runner guide.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified scenario reports.
- [`scenario1-real.log`](./scenario1-real.log), [`scenario2-failing-ref.log`](./scenario2-failing-ref.log), [`scenario3-zero-tests.log`](./scenario3-zero-tests.log), [`scenario4-sigint.log`](./scenario4-sigint.log), [`test-list.log`](./test-list.log) — Normalised scenario logs.
