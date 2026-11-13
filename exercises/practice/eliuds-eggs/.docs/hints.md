# Hints for Eliud's Eggs

This exercise asks you to count the number of `1` bits (population count) in the binary representation of a number.

## Understanding the Contract

The test cases define the exact behavior expected:

| Test Case | Input | Binary | Expected Output | Explanation |
|-----------|-------|--------|-----------------|-------------|
| `0 eggs` | `0` | `0` | `0` | Zero has no bits set |
| `1 egg` | `16` | `10000` | `1` | Single bit at position 4 |
| `4 eggs` | `89` | `1011001` | `4` | Bits at positions 0, 3, 4, 6 |
| `13 eggs` | `2000000000` | `111011100110101100101000000000` | `13` | Large number with 13 bits set |

## Key Insights

1. **Input is an integer** - The function receives `int display_value` and must return the count of 1-bits.

2. **No standard library bit-count** - The instructions explicitly forbid using built-in population count functions (like `__builtin_popcount` or `std::popcount`).

3. **Basic tools only** - Use arithmetic (`%`, `/`) or bitwise operations (`&`, `>>`) to count bits.

## C++ Representation

The reference implementation uses simple arithmetic:
```cpp
int counter{};
while (display_value != 0) {
    if (display_value % 2) ++counter;
    display_value /= 2;
}
return counter;
```

This works by:
- Checking the least significant bit with `% 2`
- Shifting right by dividing by 2
- Continuing until all bits are processed

## What Is NOT Specified

The exercise leaves these behaviors unspecified:
- **Negative inputs** - Not tested; behavior is undefined
- **Integer size** - Tests use values fitting in standard `int`
- **Performance requirements** - Only correctness is tested

## Walkthrough: 4 Eggs (89)

```
89 in binary: 1011001
             ││││││└─ position 0: 1 ✓
             │││││└── position 1: 0
             ││││└──── position 2: 0
             │││└───── position 3: 1 ✓
             ││└────── position 4: 1 ✓
             │└─────── position 5: 0
             └──────── position 6: 1 ✓
Total: 4 bits set
```

The function correctly returns `4`.