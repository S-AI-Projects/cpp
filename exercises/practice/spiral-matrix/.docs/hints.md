# Hints

## Contract Walkthrough for Subtle Spiral Matrix Cases

The spiral matrix contract specifies generating an $N \times N$ square matrix filled with natural numbers starting from `1` in the top-left corner and proceeding in an inward, clockwise spiral order.

### Decision Table

The table below connects each edge-case input condition to its exact expected C++ representation:

| Input Condition | Test Case Name | Input `size` | Expected C++ Output (`std::vector<std::vector<uint32_t>>`) | Traversal Explanation |
| :--- | :--- | :--- | :--- | :--- |
| Zero dimension ($0 \times 0$) | `empty spiral` | `0` | `{}` | Matrix with 0 rows and 0 columns; represented by an empty outer vector. |
| Single cell ($1 \times 1$) | `trivial spiral` | `1` | `{{1}}` | Matrix with 1 row and 1 column containing the single value `1`. |
| Minimal loop ($2 \times 2$) | `spiral of size 2` | `2` | `{{1, 2}, {4, 3}}` | Clockwise perimeter: row 0 `[1, 2]`, row 1 column 1 `[3]`, row 1 column 0 `[4]`. |

### Detailed Case Analysis

#### 1. Empty Spiral (`size = 0`)
- **Input**: `0`
- **Output**: `std::vector<std::vector<uint32_t>>{}`
- **Reasoning**: An empty matrix contains zero cells ($0 \times 0 = 0$). In C++, an empty collection of rows is accurately modeled by a default-constructed outer vector of size `0`. No loop execution or coordinate movement occurs.

#### 2. Trivial Spiral (`size = 1`)
- **Input**: `1`
- **Output**: `std::vector<std::vector<uint32_t>>{{1}}`
- **Reasoning**: A $1 \times 1$ matrix contains exactly one cell. The sequence begins at `1` at coordinate `(0, 0)`. Because all boundaries are immediately reached, no turns or further steps are taken.

#### 3. Spiral of Size 2 (`size = 2`)
- **Input**: `2`
- **Output**: `std::vector<std::vector<uint32_t>>{{1, 2}, {4, 3}}`
- **Reasoning**:
  1. Start at `(0, 0)` moving East: place `1`.
  2. Advance to `(0, 1)`: place `2`. Hitting right boundary triggers a 90° clockwise turn South.
  3. Advance to `(1, 1)`: place `3`. Hitting bottom boundary triggers a 90° clockwise turn West.
  4. Advance to `(1, 0)`: place `4`. Hitting left boundary / filled cells finishes the traversal.

### Scope of the Exercise Contract & Unspecified Behavior

- **Input Types**: The function signature takes `uint32_t size`. Because `size` is unsigned, negative numbers are outside the typed domain.
- **Exceptions & Errors**: No custom exceptions, assertions, or error-handling wrappers (`std::optional`, `std::expected`) are required by the problem specification.
- **Dimensions**: The contract strictly defines square matrices ($N \times N$). Rectangular matrices ($M \times N$) are outside the exercise specification.
- **Ordering**: Numbers strictly start at `1` and increment consecutively by `1` up to $N^2$.
