# Hints for Eliud's Eggs

This exercise asks you to count the number of 1 bits in the binary representation of an integer (also known as "population count" or "popcount").

## The Contract

The exercise specification defines the encoding:
1. Each potential egg spot is a bit: `1` = egg present, `0` = empty
2. The binary number is converted to decimal for the display
3. Your function must return the actual egg count = number of 1 bits

## Selected Cases Walkthrough

### 0 eggs
**Input:** `0` (decimal) = `0` (binary)
- Binary: `0`
- 1-bits: 0
- **Expected output:** `0`

This is the base case: empty coop, display shows 0.

### 1 egg
**Input:** `16` (decimal) = `10000` (binary)
- Binary: `10000`
- 1-bits: 1 (only the 5th bit from right, representing 2⁴)
- **Expected output:** `1`

A single egg in position 16 (2⁴). The reference implementation correctly counts this by repeatedly dividing by 2 and checking the remainder.

### 4 eggs
**Input:** `89` (decimal) = `1011001` (binary)
- Binary: `1011001`
- 1-bits: 4 (positions: 2⁶, 2⁴, 2³, 2⁰)
- **Expected output:** `4`

This matches Example 1 from the introduction:
```
 _ _ _ _ _ _ _
|E| |E|E| | |E|
```
Binary: `1011001` = 89 decimal, 4 eggs.

### 13 eggs (edge case)
**Input:** `2000000000` (decimal) = `111011100110101100101000000000` (binary)
- Binary has 13 ones
- **Expected output:** `13`

Tests handling of larger integers within `int` range.

## C++ Implementation Notes

The reference implementation uses a simple loop:
```cpp
int counter{};
while (display_value != 0) {
    if (display_value % 2) ++counter;
    display_value /= 2;
}
return counter;
```

This works because:
- `display_value % 2` extracts the least significant bit (1 if odd, 0 if even)
- `display_value /= 2` shifts right by one bit
- Loop continues until all bits are processed

**Important:** The exercise explicitly forbids using standard library popcount functions (like `__builtin_popcount` or `std::popcount`).

## Behavior Outside the Contract

The exercise does not specify behavior for:
- Negative input values (the specification implies non-negative integers only)
- Values exceeding `int` range (not testable in this exercise)

The reference implementation will process negative numbers using two's complement, but this is **unspecified behavior** per the exercise contract.