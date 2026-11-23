# R20-T042 Verification & Evidence (`exercises/practice/pig-latin`)

## What Is Verified

1. **Two-Copy Preparation Reproducibility (`tools/course_checks/r20-t042.py`)**:
   - Extracts two independent clean copies of `org/main` via `git archive`, runs root CMake preparation (`cmake -S . -B b`, which invokes `build_fixup()`), verifies identical SHA-256 digests for `build_exercises/practice/pig-latin/pig_latin_test.cpp`, `pig_latin.cpp`, and `pig_latin.h`, builds `--target pig-latin`, verifies identical `--list-test-names-only` output (`23` cases), and asserts exact `1:1` bijection between `.meta/tests.toml` included UUIDs (`23`) and `[uuid]` tags in `pig_latin_test.cpp` (`23`).
   - Records that no timestamps are generated, so normalization is the identity function.
2. **Isolated Single-Exercise Verification (`work/R20-T042/check.py`)**:
   - Verifies `.meta/config.json` paths (no `editor` key), learner-stub/test immutability against `org/main`, isolated CMake build (`-DEXERCISM_RUN_ALL_TESTS=ON`), Catch2 XML execution (`23/23` cases pass, including `"word beginning with a"`, `"word beginning with e"`, `"word beginning with i"`), and negative controls (`assertion_failure`, `zero_tests`, `child_failure`).
3. **`configlet sync` Status**:
   - Executed `./bin/fetch-configlet` (`configlet 4.0.3`) and `./bin/configlet sync --tests --exercise pig-latin` (without `--update`) in an isolated temp clone: `tests.toml` matches `pig_latin_test.cpp` (`23/23` UUIDs) at commit `8d139cb04c7463722ae1f233099cc0bd39a71092`; upstream `problem-specifications` added `2` newer `"a whole phrase"` cases (`44616581-5ce3-4a81-82d0-40c7ab13d2d0` and `44616581-5ce3-4a81-82d0-40c7ab13d2d1`) after the pinned commit.

## How to Run

```bash
python3 tools/course_checks/r20-t042.py --exercise pig-latin
python3 work/R20-T042/check.py
```

## Last Result

```text
RESULT: PASS - executed 23 cases
```

## Evidence Index

- [`check.py`](./check.py) & [`../../tools/course_checks/r20-t042.py`](../../tools/course_checks/r20-t042.py) — Verification & reusable preparation tool.
- [`notes.md`](./notes.md) — Track generator inspection, configlet sync output, and anchor-case mapping.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified reports.
- [`reproducibility-tool.log`](./reproducibility-tool.log), [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
