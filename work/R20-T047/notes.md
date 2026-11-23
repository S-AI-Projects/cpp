# R20-T047 Study Notes — `trinary` C++-Specific Guidance

## 1. Inspected Files

- `exercises/practice/trinary/.docs/instructions.md` (lines 1–19): Convert trinary string (`'0'`, `'1'`, `'2'`) to decimal from first principles; invalid inputs return `0`.
- `exercises/practice/trinary/.meta/config.json` (lines 1–29): `solution`: `["trinary.cpp", "trinary.h"]`, `test`: `["trinary_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/trinary/trinary.cpp` & `trinary.h`: Unsolved learner stubs.
- `exercises/practice/trinary/.meta/example.cpp` (lines 1–17) & `.meta/example.h` (lines 1–9):
  - `int to_decimal(std::string const &text)` (`example.cpp:5`): takes a `const&` to `std::string` (zero-copy read-only borrow, no ownership transfer).
  - Iterates `for (const char digit : text)` (`example.cpp:7`), rejects `digit < '0' || digit > '2'` with `return 0;` (`lines 8-10`), accumulates `result *= 3; result += digit - '0';` (`lines 11-12`) in signed `int`.
- `exercises/practice/trinary/.meta/tests.toml` (lines 1–36): `11` canonical entries, all included (including 3 separate invalid-input entries).
- `exercises/practice/trinary/trinary_test.cpp` (lines 1–34): `9` hand-written `TEST_CASE`s (no UUID tags; combines invalid cases under `"invalid_yields_decimal_0"` at `lines 31-33`).

## 2. Issue #48 Typos Identified

1. Issue #48 Step 1 names `exercises/practice/trinary/test/tests-main.cpp` instead of `exercises/practice/trinary/trinary_test.cpp`.
2. Issue #48 "Done when" lists `"so comments can be added in a \"comment\" key."` (from `tests.toml:3` header comment) instead of the actual first three test names: `"_1_yields_decimal_1"`, `"_2_yields_decimal_2"`, `"_10_yields_decimal_3"`.

## 3. Micro-Example Verification Plan

- `hints.md` provides a standalone `std::string const&` + `digit - '0'` + `std::numeric_limits<int>::max()` micro-example (` ```cpp `) and exact expected output (` ```text `), plus pitfall contrast (`numeric=1` vs `pitfall_without_minus_zero=49`), avoiding signed-overflow UB.
- `work/R20-T047/check.py` extracts both fenced blocks directly from `hints.md`, compiles the C++ snippet with `c++ -std=c++17 -Wall -Wextra -Wpedantic -Werror`, executes it, and asserts exact stdout equality against the ` ```text ` block.
