# R20-T044 Verification & Readability Refactor Summary (`exercises/practice/anagram`)

## Readability Improvement

In `exercises/practice/anagram/.meta/example.cpp`:
- **Shadowing removal & hoisted invariant state:** Renamed the parameter `matches` (which shadowed the method name `anagram::matches`) to `candidates`, hoisted `const string lowered_subject = to_lower_copy(subject_);` out of the candidate loop, and extracted `is_anagram_candidate(candidate, lowered_subject, subject_key)` with a short invariant comment explaining the exact matching contract (identical case-insensitive letter multiset `key_`, excluding the word itself case-insensitively).
- **Preserved behavior & API:** `.meta/example.h` (`anagram.h` API), return types, input-order preservation, and edge-case semantics are unchanged.

## How to Run

```bash
python3 work/R20-T044/check.py
```

## Last Result

```text
RESULT: PASS - executed 16 cases
```

## Evidence Index

- [`check.py`](./check.py) — Isolated before/after Catch2 verification, C++ equivalence harness across a fixed multi-case corpus, and negative controls.
- [`notes.md`](./notes.md) — Named case trace and refactor notes.
- [`versions.json`](./versions.json), [`inputs.json`](./inputs.json), [`counts.json`](./counts.json), [`results.xml`](./results.xml), [`before-results.xml`](./before-results.xml), [`expected-vs-actual.json`](./expected-vs-actual.json), [`negative-controls.json`](./negative-controls.json) — Machine-verified artifacts.
- [`cmake-configure.log`](./cmake-configure.log), [`cmake-build.log`](./cmake-build.log), [`cmake-build-target.log`](./cmake-build-target.log), [`test-run.log`](./test-run.log), [`test-list.log`](./test-list.log), [`equivalence-harness.log`](./equivalence-harness.log), [`negative-assertion.log`](./negative-assertion.log), [`negative-zero-tests.log`](./negative-zero-tests.log) — Normalised command logs.
