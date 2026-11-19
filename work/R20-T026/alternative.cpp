#include <cctype>
#include <map>
#include <string>

#include "word_count.h"

namespace word_count {

// Alternative approach: single-pass direct character scanner.
// Instead of creating intermediate normalized strings and vector token buffers,
// this approach identifies words directly using index boundaries and copies
// normalized words straight into the frequency map.
std::map<std::string, int> words(std::string const& text) {
    std::map<std::string, int> counts;
    std::size_t i = 0;
    const std::size_t n = text.size();

    while (i < n) {
        // Skip non-word delimiters
        while (i < n && !std::isalnum(static_cast<unsigned char>(text[i]))) {
            ++i;
        }
        if (i >= n) break;

        std::size_t start = i;
        // Scan word tokens allowing internal apostrophes (contractions)
        while (i < n) {
            char c = text[i];
            if (std::isalnum(static_cast<unsigned char>(c))) {
                ++i;
            } else if (c == '\'' && i + 1 < n && std::isalnum(static_cast<unsigned char>(text[i + 1])) && i > start) {
                // Internal apostrophe part of a contraction
                ++i;
            } else {
                break;
            }
        }

        std::string word;
        word.reserve(i - start);
        for (std::size_t j = start; j < i; ++j) {
            word.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(text[j]))));
        }

        if (!word.empty()) {
            ++counts[word];
        }
    }

    return counts;
}

}  // namespace word_count
