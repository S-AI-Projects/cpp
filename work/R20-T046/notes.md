# R20-T046 Study Notes — `alphametics` Two Approaches

## 1. Inspected Files

- `exercises/practice/alphametics/.docs/instructions.md` (lines 1–29): Replace distinct letters with distinct digits `0..9` such that the addition holds and multi-digit words never start with `0`.
- `exercises/practice/alphametics/.meta/config.json` (lines 1–19): `solution`: `["alphametics.cpp", "alphametics.h"]`, `test`: `["alphametics_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/alphametics/alphametics.cpp` & `.h`: Unsolved learner stubs (`// TODO: add your solution here`).
- `exercises/practice/alphametics/.meta/example.cpp` (lines 1–97):
  - Parses `"=="` and `'+'`, builds per-letter `weight[i]` (`+10^k` on LHS, `-10^k` on RHS), then runs letter-by-letter DFS (`lines 73-90`) checking `sum == 0` only at `pos == n`.
- `exercises/practice/alphametics/.meta/tests.toml` (`10` entries, all included) and `alphametics_test.cpp` (`10` `TEST_CASE`s, all tagged `[uuid]`):
  - Named cases:
    1. `"puzzle_with_three_letters"` (`"I + BB == ILL"`, `[e0c08b07-9028-4d5f-91e1-d178fead8e1a]`, `lines 8-16`) -> `I=1, B=9, L=0`
    2. `"solution_must_have_unique_value_for_each_letter"` (`"A == B"`, `[a504ee41-cb92-4ec2-9f11-c37e95ab3f25]`, `lines 20-24`) -> `std::nullopt`
    3. `"leading_zero_solution_is_invalid"` (`"ACA + DD == BD"`, `[4e3b81d2-be7b-4c5c-9a80-cd72bc6d465a]`, `lines 26-30`) -> `std::nullopt`

## 2. Second Independent Approach (`work/R20-T046/alternative.cpp` + `.h`)

- **Column-by-column carry propagation (`ColumnCarrySolver`):**
  - Aligns words by decimal column from units (`col = 0`) to MSD (`col = max_columns - 1`), aggregating `(letter_index, multiplicity)` per column so even `199`-addend puzzles evaluate in at most `10` terms per column.
  - Binds unassigned addend letters column-by-column, computes `total = partial_sum + carry`, immediately checks or uniquely deduces `result_column_letter[col] = total % 10`, and forwards `carry = total / 10`.
  - Dramatically reduces search states on multi-letter puzzles (e.g., `"SEND + MORE == MONEY"` and 10-letter puzzles) compared with leaf-only place-value DFS, at the cost of column table storage and `(col, term_idx, carry)` recursion state.
