# Hints

## Language-Specific Guidance: Const References in C++

In `parallel-letter-frequency`, the function signature is defined as:

```cpp
std::unordered_map<char, size_t> frequency(
    std::vector<std::string_view> const& texts);
```

### Language Construct: Const References (`const&`)

The input parameter `texts` is accepted by **const reference** (`std::vector<std::string_view> const&`).

- **Efficiency**: Passing by const reference avoids copying the outer `std::vector` across function boundaries, avoiding unnecessary heap allocation and $O(N)$ copying overhead.
- **Read-Only Access**: The `const` qualifier guarantees that `frequency` treats the input container as read-only. In multithreaded and parallel algorithms, read-only borrowing allows multiple worker threads to safely read from the container without data races.
- **Language Reference**: For further details on reference semantics, see [cppreference: Reference initialization](https://en.cppreference.com/w/cpp/language/reference_initialization) and [cppreference: Reference declaration](https://en.cppreference.com/w/cpp/language/reference).

### Standalone Executable Micro-Example

The following standalone C++ program illustrates passing data via a const reference contrasted with the pitfall of assuming `const&` provides deep immutability or ownership isolation:

```cpp
#include <iostream>
#include <string>
#include <vector>

// Helper accepting a const reference to avoid copying
size_t count_occurrences(const std::string& text, char target) {
    size_t count = 0;
    for (char c : text) {
        if (c == target) {
            ++count;
        }
    }
    return count;
}

int main() {
    std::string text = "banana";
    const std::string& ref = text;

    // Expression 1: Safe read through const reference
    std::cout << "Expression 1 (direct const ref): "
              << count_occurrences(ref, 'a') << std::endl;

    // Expression 2: Contrasting expression demonstrating aliasing/mutation pitfall:
    // A const reference prevents modification through 'ref', but does NOT prevent
    // modifications to the underlying storage by its owner or other aliases.
    text = "berry";
    std::cout << "Expression 2 (after source mutation): "
              << count_occurrences(ref, 'a') << std::endl;

    return 0;
}
```

### Expected Output

```
Expression 1 (direct const ref): 3
Expression 2 (after source mutation): 0
```

### Why the Outcomes Differ

In **Expression 1**, `ref` refers to `text` containing `"banana"`, counting `3` occurrences of `'a'`.
In **Expression 2**, `text` is mutated to `"berry"`. When `count_occurrences(ref, 'a')` is evaluated, `ref` reads the updated contents and yields `0`.

The outcomes differ because a C++ `const` reference is an *alias* rather than an independent copy or snapshot. It guarantees that the caller cannot mutate the object *through that reference*, but does not isolate the reference from mutations performed by the owner or other non-const aliases. In parallel processing, if the caller or a concurrently running thread were to modify the data while workers read via `const&`, a data race and undefined behavior would result.
