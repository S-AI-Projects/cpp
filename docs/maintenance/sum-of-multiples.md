# sum-of-multiples canonical case notes

This note compares three canonical cases with the maintained C++ reference in
`.meta/example.cpp`. It records current test coverage without changing canonical
case inclusion or the learner starter files.

| Canonical UUID | Canonical input | Expected | C++ test / rationale |
| --- | --- | ---: | --- |
| `54aaab5a-ce86-4edc-8b40-d3ab2400a279` | `factors=[3,5], limit=1` | `0` | `sum_to_1_yields_0` currently calls `to({3,5}, 0)`, so its name is close but its input is not the canonical limit. For limit 1, the loop visits only 0 and returns 0. |
| `361e4e50-c89b-4f60-95ef-5bc5c595490a` | `factors=[3,5], limit=4` | `3` | Covered exactly by `sum_to_4_yields_3`; the reference adds 3 when `i % 3 == 0`, then breaks so the same value cannot be counted twice. |
| `e644e070-040e-4ae0-9910-93c69fc3f7ce` | `factors=[3], limit=7` | `9` | There is no exact enabled C++ test for this input. `sum_to_10_yields_23` tests `{3,5}` below 10 and corresponds to a different canonical case. The reference supports the one-factor input: it adds 3 and 6. |

The implementation's inner loop tests each candidate with `i % multiple == 0`
and breaks after the first matching factor. That operation explains both the
sum and duplicate handling for positive factors. These three cases do not
involve a zero factor, so they avoid C++'s undefined integer remainder by zero.

## Coverage snapshot

Before and after this documentation-only change, `.meta/tests.toml` contains 16
UUID entries and 0 explicit `include = false` exclusions. The C++ test source
contains 12 test cases. The checker records both counts and verifies the three
canonical outputs directly against the reference. It also builds and runs every
enabled C++ case. No test inclusion was changed.

Run the focused check from the repository root:

```sh
python3 work/R20-T011/check.py
```

The checker copies the exercise, including its dotfiles, into a temporary
directory, substitutes the maintained reference only in that copy, then
configures, builds, and runs the test executable. It leaves the learner files
and working tree untouched.
