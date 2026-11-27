# R20-T045 Verification & Scaling Study (`exercises/practice/beer-song`)

## What Is Verified

1. **Comment-Only Change in `exercises/practice/beer-song/.meta/example.cpp`**:
   - Added a complexity/invariant comment immediately above `bottles_of_beer_on_the_wall`.
   - `strip_cpp_comments(before) == strip_cpp_comments(after)` is asserted against `org/main`.
2. **Catch2 Reference Tests (`5/5` Pass)**:
   - Runs `beer_song_test.cpp` in an isolated temp copy with `-DEXERCISM_RUN_ALL_TESTS=ON`, verifying all `5` cases pass (including `"prints_an_arbitrary_verse"`, `"handles_1_bottle"`, `"handles_0_bottles"`).
3. **Instrumented Operation Counts & In-Process Benchmark (`cost-study.json`)**:
   - Asserts exact specification text equality first, counts exact operations across `verse(8)` (`1` verse), `sing(9, 0)` (`10` verses), and `sing(99, 0)` (`100` verses), verifies that `docs/maintenance/beer-song.md` reports identical instrumented numbers, and separates compile/startup timings from algorithm timings.
4. **Negative Controls**:
   - Mutated `verse(8)` assertion failure, `0`-test Catch2 filter (`ZERO-TEST GUARD`), and non-zero child exit codes.

## How to Run

```bash
python3 work/R20-T045/check.py
```

## Last Result

```text
RESULT: PASS - executed 5 cases
```

## Evidence Index

- [`check.py`](./check.py) — Verification, comment-only diff check, instrumentation, benchmark, and negative controls.
- [`notes.md`](./notes.md) & [`../../docs/maintenance/beer-song.md`](../../docs/maintenance/beer-song.md) — Study notes and maintenance cost document.
- [`cost-study.json`](./cost-study.json), [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified artifacts.
- [`instrumentation.log`](./instrumentation.log), [`benchmark.log`](./benchmark.log), [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
