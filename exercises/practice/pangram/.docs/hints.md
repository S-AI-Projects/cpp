# Hints

## General

- Consider how to avoid expensive copies when passing strings to helper functions.
- Ensure character comparisons correctly handle casing and non-alphabetic characters.

## Const References

In `exercises/practice/pangram/.meta/example.cpp`, the helper function `found_letter` receives the target sentence `s` by **const reference** (`const std::string &s`).

```cpp
bool found_letter(char a, const std::string &s);
```

### Why Const References?

1. **Efficiency (Avoiding Copies):** A `std::string` can allocate dynamic memory and hold long text. Passing it by value (`std::string s`) creates a full copy of the string every time `found_letter` is called (which happens up to 26 times in this implementation). Passing by reference (`&`) passes an alias to the existing string without copying memory.
2. **Read-Only Safety (`const`):** The `const` qualifier guarantees that `found_letter` cannot accidentally modify the caller's string.
3. **Binding to Temporaries and Literals:** A `const` reference allows callers to pass temporary string objects or expressions directly (e.g., `found_letter('a', std::string("test"))`).

---

### Safe Example: Passing by Const Reference

Passing the string by `const std::string&` avoids copying the input string when searching for a character:

```cpp
#include <cctype>
#include <iostream>
#include <string>

// Checks if character 'target' exists in 'text' without copying 'text'
bool found_letter(char target, const std::string &text) {
    for (char c : text) {
        if (std::tolower(static_cast<unsigned char>(c)) == target) {
            return true;
        }
    }
    return false;
}

int main() {
    std::string sentence = "The quick brown fox jumps over the lazy dog.";
    bool found_z = found_letter('z', sentence);
    bool found_exclamation = found_letter('!', sentence);

    std::cout << std::boolalpha;
    std::cout << "Found 'z': " << found_z << "\n";
    std::cout << "Found '!': " << found_exclamation << "\n";
    return 0;
}
```

#### Expected Output/Behavior:
```text
Found 'z': true
Found '!': false
```
The function safely scans the original string `sentence` without copying, correctly returning `true` for present characters and `false` for absent ones.

---

### Pitfall Example: Unchecked Arithmetic / Out-of-Bounds Shift

A common alternative tracking approach maps letters to indices by subtracting `'a'` (or `'A'`) to set bits in an integer bitmask (e.g., `1u << (c - 'a')`). However, if non-lowercase or non-alphabetic characters (such as uppercase letters, punctuation, or spaces) are not filtered out first, this causes an underflow or invalid bit shift:

```cpp
#include <iostream>

int main() {
    char ch = ' '; // Space character (ASCII 32)
    
    // Pitfall: Subtracting 'a' (ASCII 97) without checking std::isalpha
    int shift_amount = ch - 'a'; // 32 - 97 = -65
    
    std::cout << "Shift amount for space: " << shift_amount << "\n";

    // Attempting a bit shift by a negative count causes undefined behavior:
    // unsigned int mask = 1u << shift_amount; // UNDEFINED BEHAVIOR
    
    return 0;
}
```

#### Expected Output/Behavior:
```text
Shift amount for space: -65
```
Because `' '` (ASCII 32) is less than `'a'` (ASCII 97), `ch - 'a'` evaluates to `-65`. In C++, shifting by a negative value or by a value greater than or equal to the width of the type is **undefined behavior** (often resulting in program crashes, CPU exceptions, or unexpected bitmask corruption).
