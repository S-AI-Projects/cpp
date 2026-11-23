# Hints

## General

- Read digits from left to right: start an accumulator at `0` and, for each valid trinary digit `'0'`, `'1'`, or `'2'`, multiply the accumulator by `3` and add the digit's numeric value (`0`, `1`, or `2`).
- Return `0` immediately if any character outside `'0'..'2'` appears in the input.

## C++ Constructs in `trinary`

The maintained reference signature in `to_decimal` is:

```cpp
int to_decimal(std::string const& text)
```

Three C++ details directly govern correctness and efficiency here:

1. **Read-only borrowing via `std::string const&`:** Taking the input by `const` lvalue reference avoids copying the caller's string and communicates that `to_decimal` neither mutates `text` nor takes ownership of it (the caller's string stays valid across the call).
2. **Character-to-digit arithmetic (`digit - '0'`):** Elements of `std::string` are `char` code units, not numeric integers `0..2`. Subtracting `'0'` shifts the contiguous ASCII digit codes (`'0'` = `48`, `'1'` = `49`, `'2'` = `50`) to integer values `0`, `1`, and `2`.
3. **Signed `int` range and well-defined bounds:** Accumulating in a signed `int` limits valid input length to values up to `std::numeric_limits<int>::max()`. Signed integer overflow is undefined behavior in C++, so range checking must happen *before* multiplying by `3` (`value > (std::numeric_limits<int>::max() - d) / 3`), not after overflowing. Also note that because invalid strings return `0`, an invalid input such as `"carrot"` and the valid input `"0"` share the same return value `0`.

### Micro-Example & Pitfall (Not a Full Solver)

The standalone snippet below demonstrates `std::string const&` borrowing (same address as caller's string, zero copy), converting a single character with `digit - '0'`, the **pitfall** of omitting `- '0'` (adding raw `char` `'1'` gives ASCII `49` instead of `1`), and a well-defined `std::numeric_limits<int>::max()` pre-multiplication guard:

```cpp
#include <iostream>
#include <limits>
#include <string>

void inspect_digit(std::string const& sample, const void* caller_addr) {
    char ch = sample.front();
    int numeric_value = ch - '0';
    int raw_char_value = static_cast<int>(ch);
    int max_int = std::numeric_limits<int>::max();
    bool safe_before_mul3 = numeric_value <= (max_int - numeric_value) / 3;

    std::cout << "same_storage=" << std::boolalpha
              << (static_cast<const void*>(&sample) == caller_addr)
              << " char='" << ch << "'"
              << " numeric=" << numeric_value
              << " pitfall_without_minus_zero=" << raw_char_value
              << " safe_mul3=" << safe_before_mul3 << "\n";
}

int main() {
    std::string caller_text = "1";
    const void* caller_addr = static_cast<const void*>(&caller_text);
    std::string const& borrowed = caller_text;
    std::cout << "zero_copy_same_addr="
              << (static_cast<const void*>(&borrowed) == caller_addr) << "\n";
    inspect_digit(caller_text, caller_addr);
    return 0;
}
```

Expected output:

```text
zero_copy_same_addr=1
same_storage=true char='1' numeric=1 pitfall_without_minus_zero=49 safe_mul3=true
```

### Why the Pitfall Outcomes Differ

- With `ch - '0'`, `'1'` evaluates to `49 - 48 = 1` (the base-3 digit value).
- Without subtracting `'0'`, `ch` undergoes integral promotion to `int` as its ASCII character code (`49`), inflating any calculation by `48` per digit.

### Language References

- [Reference declaration (`const&` parameter passing)](https://en.cppreference.com/w/cpp/language/reference)
- [`std::numeric_limits<int>::max()`](https://en.cppreference.com/w/cpp/types/numeric_limits)
