# Maintenance of Kindergarten Garden Tests

## Test Maintenance Approach

The tests for the `kindergarten-garden` exercise are maintained in `kindergarten_garden_test.cpp`.

## Deliberate Code Mutant Analysis

To verify test suite effectiveness, deliberate mutations can be applied to the reference implementation in `example.cpp`.

### Mutant Description

In `kindergarten_garden::plants`, each student is assigned 4 plants (a 2x2 grid, with 2 consecutive cups on the top row and 2 consecutive cups on the bottom row).
A student at 0-based alphabetical index $i$ corresponds to cups starting at horizontal offset $2 \times i$:
- Top row: index `2 * i` and `2 * i + 1`
- Bottom row: index `(row_len + 1) + 2 * i` and `(row_len + 1) + 2 * i + 1`

Consider a deliberate mutant that incorrectly computes the student's horizontal column index by omitting the multiplication factor of 2:

```cpp
// Original:
const int first_plant_index = 2 * (student.at(0) - 'A');

// Mutant:
const int first_plant_index = 1 * (student.at(0) - 'A');
```

Alternatively, changing `2 * (student.at(0) - 'A')` to `(student.at(0) - 'A')`.

### Test Case Rejection

- For **Alice** (`student.at(0) == 'A'`), index is 0, so `2 * 0 == 1 * 0 == 0`. The single student test cases (such as `"garden with single student"`, `"different garden with single student"`, and `"for Alice, first student's garden"`) will not detect this fault.
- For **Bob** (`student.at(0) == 'B'`), `student.at(0) - 'A' == 1`.
  - The correct index is `2 * 1 = 2`.
  - The mutated index is `1 * 1 = 1`.
- The test case **`garden with two students`** (UUID: `c376fcc8-349c-446c-94b0-903947315757`):
  ```cpp
  REQUIRE(kindergarten_garden::plants("VVCG\nVVRC", "Bob") == expected);
  ```
  - Expected plants for Bob at indices `[2, 3]` and `[7, 8]`: `'C'`, `'G'`, `'R'`, `'C'` (`clover`, `grass`, `radishes`, `clover`).
  - Mutated indices evaluate to `[1, 2]` and `[6, 7]`: `'V'`, `'C'`, `'V'`, `'R'` (`violets`, `clover`, `violets`, `radishes`).
  - Therefore, the test case **`"garden with two students"`** explicitly fails and rejects this mutant.
