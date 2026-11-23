# R20-T041 Verification & Evidence (`exercises/practice/knapsack`)

## What Is Verified

1. **Canonical Case Inventory & Rationales (`exercises/practice/knapsack/.meta/tests.toml`)**:
   - All `8` canonical entries (`7` included, `1` excluded) parse cleanly with both `tomllib` (Python 3.11+) and the Python 3.9+ standard-library fallback parser.
   - `include` and `reimplements` fields are unchanged relative to `org/main` (`8 total / 7 included / 1 excluded`).
   - Excluded UUID `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` (`"no items"`, `include = false`) is classified as a **replacement case** superseded by `3993a824-c20e-493d-b3c9-ee8a7753ee59` (`reimplements = "a4d7d2f0-ad8a-460c-86f3-88ba709d41a7"`), which corrected `input.items` from `{}` to `[]` in `problem-specifications`.
   - Persistent `comment = "..."` keys (preserved by `configlet sync`) are present on `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` and the three named UUIDs (`3993a824-c20e-493d-b3c9-ee8a7753ee59`, `1d39e98c-6249-4a8b-912f-87cb12e506b0`, `833ea310-6323-44f2-9d27-a278740ffbd8`).
   - All `7` included UUIDs match the `[maximumValue][<uuid>]` tags in `exercises/practice/knapsack/knapsack_test.cpp`.
2. **Isolated Reference Build & Execution**:
   - Copies `exercises/practice/knapsack` (including `.meta`, `.docs`, and `test/catch.hpp`) to an isolated temporary directory (`r20-t041-*`), substitutes `.meta/example.cpp` -> `knapsack.cpp` and `.meta/example.h` -> `knapsack.h` by matching extension, configures CMake with `-DEXERCISM_RUN_ALL_TESTS=ON`, builds `knapsack`, runs Catch2 XML output and `--list-test-names-only`, and verifies all `7` cases (including the `3` named cases) pass.
3. **Learner File Protection**:
   - Verifies `knapsack.cpp`, `knapsack.h`, `knapsack_test.cpp`, and `.docs/instructions.md` are byte-identical to `org/main`, SHA-256 hashes every file under `exercises/practice/knapsack` before and after in `finally:`, and verifies the temporary directory is removed.
4. **Negative Controls**:
   - **Assertion failure**: Mutating the reference in the temp copy so `"no items"` returns `-1` causes the test executable to exit non-zero and `evaluate()` to report failure on `"no items"`.
   - **Zero-test guard**: Running the executable with filter `"no-such-test-filter*"` causes Catch2 v2.13.6 to exit `0` with `0` cases, which `evaluate()` rejects via the `ZERO-TEST GUARD`.
   - **Child failure**: Passing a non-zero `build_rc` or `run_rc` with an otherwise passing XML document is rejected by `evaluate()`.

## How to Run

From the repository root:

```bash
python3 work/R20-T041/check.py
```

## Last Result

```text
RESULT: PASS - executed 7 cases
```

## Evidence Index

- [`check.py`](./check.py) — Python 3.9+ standard-library check script.
- [`notes.md`](./notes.md) — Inspection notes tracing `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` -> `3993a824-c20e-493d-b3c9-ee8a7753ee59` -> `knapsack_test.cpp` -> `.meta/example.cpp`.
- [`versions.json`](./versions.json) — Python, CMake, Apple Clang, Catch2, OS, and Git commit versions.
- [`inputs.json`](./inputs.json) — Resolved `.meta/config.json` paths, named cases, and before/after SHA-256 hashes of all files under `exercises/practice/knapsack`.
- [`counts.json`](./counts.json) — Static `TEST_CASE` count (`7`), Catch2 XML case count (`7`), `--list-test-names-only` count (`7`), and `tests.toml` before/after counts (`8/7/1` -> `8/7/1`).
- [`results.xml`](./results.xml) — Catch2 XML report (`7` passed, `0` failed) with paths normalised to `<TMP>` / `<REPO>`.
- [`expected-vs-actual.json`](./expected-vs-actual.json) — Per-case expected vs actual pass results, named-case flags, and excluded UUID rationale.
- [`negative-controls.json`](./negative-controls.json) — Verification of assertion-failure, zero-test-filter, and non-zero child-exit controls.
- [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
