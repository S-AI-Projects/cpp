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
