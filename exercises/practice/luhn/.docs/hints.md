# Hints

## Read the number without copying it

The reference function takes `std::string const& input_str`. This is a read-only reference to the caller's string: `valid` can inspect a long input without making a separate string copy, and the parameter does not allow the function to edit the caller's characters. The reference is used only while `valid` runs; do not keep a reference to a local string after its lifetime ends. See [C++ reference declarations](https://en.cppreference.com/w/cpp/language/reference).

### C++ micro-example

The exercise allows spaces but ignores them when counting digits from the right. A raw string length therefore differs from the digit count used to choose which digits to double:

```cpp
#include <iostream>
#include <string>

std::size_t count_digits(const std::string& input) {
    std::size_t digits = 0;
    for (auto it = input.rbegin(); it != input.rend(); ++it) {
        if (*it == ' ') continue;
        if (*it < '0' || *it > '9') return 0;
        ++digits;
    }
    return digits;
}

int main() {
    const std::string number = "0 59";
    std::cout << number.size() << '\n';
    std::cout << count_digits(number) << '\n';
}
```

Output:

```text
4
3
```

The first line counts the space; the second counts only digits. For Luhn parity, advance the every-other-digit counter only after a digit. Counting the space shifts which digit is doubled. The example is deliberately limited to counting and does not implement the full validator.
