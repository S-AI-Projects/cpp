# Hints

## General

- Parse the equation into addends on the left of `==` and the target sum word on the right.
- At most `10` distinct letters can appear in a valid base-10 puzzle; any letter that begins a multi-letter word cannot take digit `0`.

## Choosing an approach

Two distinct solver designs both satisfy the `alphametics::solve` contract (`std::optional<std::map<char, int>>`):

### 1. Place-value weight vector + letter-order DFS (global linear equation)

- **Representation:** Collapse every word occurrence into a single signed `long long` weight per letter (adding $10^k$ on the left of `==` and subtracting $10^k$ on the right).
- **Control flow:** Recursively assign one distinct digit (`0..9`, skipping `0` for leading letters) to each letter in discovery order and test `weighted_sum == 0` once all `n` letters are bound.
- **Trade-off:** Very compact state (`O(n)` weight vector and one running `long long` sum) and fast arithmetic per step, especially when many addends collapse into a single weight per letter. However, invalid units/tens digits are only rejected after assigning all `n` letters, visiting up to $10!/(10-n)!$ partial states in unpruned order.

### 2. Column-by-column carry propagation (local arithmetic pruning)

- **Representation:** Store each decimal column from right (units, $10^0$) to left (`max_columns - 1`), grouping `(letter, count)` multiplicities on the left side alongside the right-hand target letter for that column.
- **Control flow:** Recursively bind only the unassigned addend letters in the current column, compute `total = col_sum + carry`, immediately deduce or check `needed = total % 10` for the right-hand letter, reject conflicts at once, and forward `carry = total / 10` to the next column.
- **Trade-off:** Requires column-aligned tables and `(col, term, carry)` recursion state, which uses slightly more setup code and per-column storage (`O(columns * distinct_letters)`). In return, it prunes impossible partial assignments at the earliest column and uniquely deduces each result digit in `O(1)` without searching over it.

### Worked Trace on `"I + BB == ILL"`

1. **Leading-letter constraint:** `'B'` (from `"BB"`) and `'I'` (from `"ILL"`) have word length $> 1$, so `B != 0` and `I != 0`. `'L'` is not a leading letter.
2. **Place-value representation:**
   - Addends: `I * 1` + `B * (10 + 1)` = `I + 11*B`.
   - Result: `I * 100 + L * 10 + L * 1` = `100*I + 11*L`.
   - Net equation: `11*B - 99*I - 11*L = 0`, i.e., `B = 9*I + L`. Since `B <= 9` and `I >= 1`, `I` must be `1`, `L` must be `0`, and `B` must be `9`.
3. **Column-by-column carry trace (right to left):**
   - **Column 0 (units):** `I + B = L + 10 * carry_1`. For `I = 1`, `B = 9`: `1 + 9 = 10`, which deduces `L = 0` (`unused`, non-leading -> valid!) and `carry_1 = 1`.
   - **Column 1 (tens):** `B + carry_1 = L + 10 * carry_2` -> `9 + 1 = 10`, matching `L = 0` with `carry_2 = 1`.
   - **Column 2 (hundreds):** `carry_2 = I` -> `1 == 1` with `carry_3 = 0`.
   - **Result:** `{B: 9, I: 1, L: 0}` (`1 + 99 == 100`).
