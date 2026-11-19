# Hints

## General

- Remember that prime numbers start at 2 (1 is not prime).
- The function receives a 1-based index `n`.
- For $n < 1$ (such as $n = 0$ or negative integers), the problem contract requires throwing `std::domain_error` from the standard header `<stdexcept>`.

## C++ Language-Specific Guidance

### Standard Headers and Types

- [`<stdexcept>`](https://en.cppreference.com/w/cpp/header/stdexcept): Provides `std::domain_error`, which must be thrown when $n < 1$.
- [`<vector>`](https://en.cppreference.com/w/cpp/header/vector): Can be used to accumulate discovered primes and test subsequent odd candidates against existing primes.
- [`<cmath>`](https://en.cppreference.com/w/cpp/header/cmath): Provides `std::sqrt` to bound trial division up to $\lfloor\sqrt{x}\rfloor$.

### Performance Consideration & Constraints

Testing divisibility only up to $\sqrt{x}$ significantly reduces time complexity:
- A naive check testing all numbers up to $x$ runs in $\mathcal{O}(x)$ per candidate.
- Bounding by $\sqrt{x}$ with `std::sqrt` runs in $\mathcal{O}(\sqrt{x})$ per candidate.
- Skipping even numbers after checking 2 halves the candidate search space.

### Executable Micro-Example

The following standalone C++ example demonstrates trial division bounded by `std::sqrt` with domain error handling:

```cpp
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

bool is_prime(int candidate) {
    if (candidate < 2) return false;
    if (candidate == 2) return true;
    if (candidate % 2 == 0) return false;
    int limit = static_cast<int>(std::sqrt(candidate));
    for (int d = 3; d <= limit; d += 2) {
        if (candidate % d == 0) return false;
    }
    return true;
}

int nth_prime(int n) {
    if (n < 1) {
        throw std::domain_error("Argument must be at least 1");
    }
    int count = 0;
    int candidate = 1;
    while (count < n) {
        ++candidate;
        if (is_prime(candidate)) {
            ++count;
        }
    }
    return candidate;
}

int main() {
    std::cout << "1st prime: " << nth_prime(1) << "\n";
    std::cout << "2nd prime: " << nth_prime(2) << "\n";
    std::cout << "6th prime: " << nth_prime(6) << "\n";
    return 0;
}
```

### Expected Output

```text
1st prime: 2
2nd prime: 3
6th prime: 13
```

### Reference Documentation

- [C++ std::domain_error reference](https://en.cppreference.com/w/cpp/error/domain_error)
- [C++ std::sqrt reference](https://en.cppreference.com/w/cpp/numeric/math/sqrt)
