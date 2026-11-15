# Hints

## General

- Consider what the allergy test score represents: each allergen is assigned a distinct power of 2 ($1, 2, 4, 8, 16, \dots$).
- Because scores are formed by summing powers of 2, determining active allergies is equivalent to inspecting which binary powers make up the given score.

## Approaches to Consider

### 1. Bitwise Masking (Direct Bit Inspection)

Because each item's numerical score is a unique power of two ($2^n$), each allergen corresponds to a single bit flag in the binary representation of the integer:
- Eggs ($1 = 2^0$): bit 0
- Peanuts ($2 = 2^1$): bit 1
- Shellfish ($4 = 2^2$): bit 2, and so forth.

With this approach:
- You store the integer score directly as an internal member variable.
- Testing membership (`is_allergic_to`) checks whether the corresponding bit is set using the bitwise AND operator (`&`). For example, `(score & item_mask) != 0` or `(score & item_mask) == item_mask`.
- Computing all allergies iterates over known allergen bit flags and collects matching names into a set.

### 2. Arithmetic Decomposition with Precomputed Set

Instead of using low-level bitwise manipulation operators, you can treat the score as an arithmetic quantity decomposed into powers of 2 using repeated division and modulo arithmetic:
- In the constructor, repeatedly inspect the least significant component with `% 2` and step down with `/ 2`.
- When `remaining % 2 == 1`, the allergen corresponding to the current power is active and added to an internal `std::unordered_set<std::string>`.
- Any remaining value beyond the known allergens can be discarded automatically once all known items have been checked.

### A Worked Example: Score of 3 (Eggs and Peanuts)

Suppose a person has a score of `3`:

- **Under Bitwise Masking:**
  - `score = 3` (binary `00000011`).
  - Eggs mask is `1` (binary `00000001`). Performing `3 & 1` evaluates to `1`. Since `1 == 1`, eggs is present.
  - Peanuts mask is `2` (binary `00000010`). Performing `3 & 2` evaluates to `2`. Since `2 == 2`, peanuts is present.
  - Shellfish mask is `4` (binary `00000100`). Performing `3 & 4` evaluates to `0`. Since `0 != 4`, shellfish is absent.

- **Under Arithmetic Decomposition:**
  - Step 0 (Eggs): `3 % 2 == 1` $\rightarrow$ eggs is present and inserted into the set. Update `remaining = 3 / 2 = 1`.
  - Step 1 (Peanuts): `1 % 2 == 1` $\rightarrow$ peanuts is present and inserted into the set. Update `remaining = 1 / 2 = 0`.
  - Step 2 (Shellfish): `remaining == 0` $\rightarrow$ stop early.

### Trade-offs: When is the Alternative Clearer?

- **Readability & Familiarity:**
  - Bitwise operations (`&`, `|`, `<<`) can feel unfamiliar or cryptic if you have not worked extensively with binary bitmasks.
  - The arithmetic approach (`% 2` and `/ 2`) relies on fundamental math concepts that closely mirror how numbers are converted to base 2 by hand.
  - Furthermore, caching the results inside an `std::unordered_set` makes queries like `is_allergic_to` an intuitive hash lookup (`set.count(item)` or `set.find(item) != set.end()`), and `get_allergies` simply returns the precomputed set.

- **Cost and Memory Overhead:**
  - **Memory:** Bitwise masking stores only a single primitive integer (`unsigned int`, typically 4 bytes). The precomputed set approach allocates dynamic node memory on the heap for the `std::unordered_set` (hash buckets, node pointers, string copies), consuming noticeably more memory per instance.
  - **Work / Complexity:** 
    - Bitwise masking does virtually zero upfront work in the constructor ($O(1)$) and evaluates `is_allergic_to` in $O(1)$ operations with a map/flag lookup. Constructing `get_allergies` takes $O(K)$ time where $K$ is the number of known allergens (8 items).
    - The precomputed arithmetic approach does $O(K)$ work in the constructor hashing and allocating entries into the set. While subsequent `is_allergic_to` queries are average $O(1)$, they involve hash computations and node traversals compared to a single CPU bitwise instruction.
