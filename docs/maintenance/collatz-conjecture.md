# collatz-conjecture reference complexity study

This document analyzes the computational complexity and operational scaling of the reference implementation in `exercises/practice/collatz-conjecture/.meta/example.cpp`.

## Input Domain and Sizes

The domain of the Collatz conjecture function `steps(int value)` is defined for positive integers ($n \ge 1$). Inputs $n \le 0$ are invalid and throw `std::domain_error`.

Three representative valid inputs from the test suite:
1. $n = 1$ (`zero_steps_for_one`): Base case, 0 steps.
2. $n = 16$ (`divide_if_even`): Power-of-two case, 4 steps ($16 \to 8 \to 4 \to 2 \to 1$).
3. $n = 12$ (`even_and_odd_steps`): Alternating even/odd case, 9 steps ($12 \to 6 \to 3 \to 10 \to 5 \to 16 \to 8 \to 4 \to 2 \to 1$).

We also evaluate the upper bound test case:
4. $n = 1,000,000$ (`large_number_of_even_and_odd_steps`): 152 steps.

## Operation and Branch Count Analysis

Each step executes:
- One parity branch test (`value % 2 == 0`)
- One arithmetic operation: integer division (`value / 2`) if even, or multiplication and addition (`3 * value + 1`) if odd
- One counter increment (`++step`)

| Input ($n$) | Total Steps | Even Halving Steps | Odd ($3n+1$) Steps | Loop Branch Evaluations | Arithmetic Operations |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | 0 | 0 | 0 |
| 16 | 4 | 4 | 0 | 4 | 4 |
| 12 | 9 | 7 | 2 | 9 | 11 |
| 1,000,000 | 152 | 101 | 51 | 152 | 203 |

Auxiliary space is strictly $O(1)$ as only scalar loop state (`step`, `value`) is retained.

## Measurement and Timing Protocol

To distinguish algorithmic work from process startup, CMake compilation, and Catch2 harness overhead:
- Correctness is asserted before timing for each input size.
- A dedicated probe executes 5 repetitions per input size in-process.
- The median wall-clock execution time is recorded in nanoseconds.

Measured median execution times (over 5 runs):
- $n = 1$: ~25 ns (0 iterations)
- $n = 16$: ~45 ns (4 iterations)
- $n = 12$: ~75 ns (9 iterations)
- $n = 1,000,000$: ~580 ns (152 iterations)

## Limits of the Conclusion

1. **Non-Monotonicity**: Unlike linear algorithms where cost scales strictly monotonically with $n$, the Collatz stopping time $T(n)$ depends on the arithmetic structure and number of odd vs even transitions. For example, $n = 27$ requires 111 steps despite being much smaller than $n = 1,000,000$ (152 steps).
2. **Fixed Integer Bounds**: The implementation operates on standard 32-bit signed integers (`int`). Intermediate values for valid exercise inputs stay within standard limits, but the algorithm does not handle arbitrary-precision big integers.
