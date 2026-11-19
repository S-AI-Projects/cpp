#include <stdexcept>

#include "collatz_conjecture.h"

// Complexity and Invariants:
// - Space Complexity: O(1) auxiliary space (using a constant number of scalar integer variables).
// - Time Complexity: O(T(n)) operations, where T(n) is the total stopping time of the Collatz sequence.
//   For pure powers of two (e.g., n = 2^k), T(n) = k = log2(n) iterations.
//   Each iteration performs exactly one parity check (value % 2 == 0) and one arithmetic transition
//   (halving for even values or 3*value + 1 for odd values).
// - Invariant: The loop maintains value > 0 and terminates when value == 1, with step tracking
//   the exact transition count from the initial positive integer to 1.
int collatz_conjecture::steps(int value) {
    if (value <= 0)
        throw std::domain_error("Only positive numbers are allowed!");
    int step = 0;
    while (value != 1) {
        value = value % 2 == 0 ? value / 2 : 3 * value + 1;
        ++step;
    }
    return step;
}
