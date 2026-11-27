#include <algorithm>
#include <array>
#include <cstddef>
#include <string>
#include <utility>
#include <vector>

#include "alphametics.h"

namespace alphametics {
namespace {

struct ColumnTerm {
    int letter_index;
    int multiplicity;
};

struct PuzzleModel {
    std::vector<char> letters;
    std::array<bool, 10> is_leading{};
    std::vector<std::vector<ColumnTerm>> addend_columns;
    std::vector<int> result_column_letter;
    std::size_t max_columns{0};
};

std::string trim_spaces(std::string const& raw) {
    const auto first = raw.find_first_not_of(' ');
    if (first == std::string::npos) {
        return {};
    }
    const auto last = raw.find_last_not_of(' ');
    return raw.substr(first, last - first + 1);
}

bool parse_puzzle(std::string const& puzzle, PuzzleModel& model) {
    const auto eq_pos = puzzle.find("==");
    if (eq_pos == std::string::npos) {
        return false;
    }

    const std::string lhs = trim_spaces(puzzle.substr(0, eq_pos));
    const std::string rhs = trim_spaces(puzzle.substr(eq_pos + 2));
    if (lhs.empty() || rhs.empty()) {
        return false;
    }

    std::vector<std::string> addends;
    std::size_t start = 0;
    while (start <= lhs.size()) {
        const auto plus_pos = lhs.find('+', start);
        const std::string part =
            trim_spaces(plus_pos == std::string::npos
                            ? lhs.substr(start)
                            : lhs.substr(start, plus_pos - start));
        if (part.empty()) {
            return false;
        }
        addends.push_back(part);
        if (plus_pos == std::string::npos) {
            break;
        }
        start = plus_pos + 1;
    }

    std::array<int, 256> char_to_idx;
    char_to_idx.fill(-1);

    auto register_word = [&](std::string const& word) -> bool {
        if (word.size() > 1) {
            const unsigned char first_ch =
                static_cast<unsigned char>(word.front());
            if (char_to_idx[first_ch] == -1) {
                if (model.letters.size() >= 10) {
                    return false;
                }
                char_to_idx[first_ch] = static_cast<int>(model.letters.size());
                model.letters.push_back(word.front());
            }
            model.is_leading[char_to_idx[first_ch]] = true;
        }
        for (char c : word) {
            const unsigned char uc = static_cast<unsigned char>(c);
            if (char_to_idx[uc] == -1) {
                if (model.letters.size() >= 10) {
                    return false;
                }
                char_to_idx[uc] = static_cast<int>(model.letters.size());
                model.letters.push_back(c);
            }
        }
        return true;
    };

    model.max_columns = rhs.size();
    for (std::string const& word : addends) {
        if (!register_word(word)) {
            return false;
        }
        model.max_columns = std::max(model.max_columns, word.size());
    }
    if (!register_word(rhs)) {
        return false;
    }

    model.addend_columns.resize(model.max_columns);
    model.result_column_letter.assign(model.max_columns, -1);

    for (std::size_t col = 0; col < model.max_columns; ++col) {
        std::array<int, 10> counts{};
        for (std::string const& word : addends) {
            if (col < word.size()) {
                const unsigned char ch =
                    static_cast<unsigned char>(word[word.size() - 1 - col]);
                ++counts[char_to_idx[ch]];
            }
        }
        for (int li = 0; li < static_cast<int>(model.letters.size()); ++li) {
            if (counts[li] > 0) {
                model.addend_columns[col].push_back({li, counts[li]});
            }
        }
        if (col < rhs.size()) {
            const unsigned char rch =
                static_cast<unsigned char>(rhs[rhs.size() - 1 - col]);
            model.result_column_letter[col] = char_to_idx[rch];
        }
    }

    return true;
}

class ColumnCarrySolver {
   public:
    explicit ColumnCarrySolver(PuzzleModel const& model) : model_(model) {
        assigned_.fill(-1);
        used_digit_.fill(false);
    }

    bool solve() { return search(0, 0, 0, 0); }

    std::map<char, int> build_solution() const {
        std::map<char, int> out;
        for (std::size_t i = 0; i < model_.letters.size(); ++i) {
            out[model_.letters[i]] = assigned_[i];
        }
        return out;
    }

   private:
    bool search(std::size_t col, std::size_t term_idx, int carry,
                int partial_sum) {
        if (col == model_.max_columns) {
            return carry == 0;
        }

        auto const& terms = model_.addend_columns[col];
        if (term_idx < terms.size()) {
            const int li = terms[term_idx].letter_index;
            const int mult = terms[term_idx].multiplicity;
            if (assigned_[li] != -1) {
                return search(col, term_idx + 1, carry,
                              partial_sum + mult * assigned_[li]);
            }
            for (int d = 0; d <= 9; ++d) {
                if (used_digit_[d] || (d == 0 && model_.is_leading[li])) {
                    continue;
                }
                used_digit_[d] = true;
                assigned_[li] = d;
                if (search(col, term_idx + 1, carry, partial_sum + mult * d)) {
                    return true;
                }
                assigned_[li] = -1;
                used_digit_[d] = false;
            }
            return false;
        }

        const int total = partial_sum + carry;
        const int needed = total % 10;
        const int next_carry = total / 10;
        const int res_li = model_.result_column_letter[col];

        if (res_li == -1) {
            return needed == 0 && search(col + 1, 0, next_carry, 0);
        }
        if (assigned_[res_li] != -1) {
            return assigned_[res_li] == needed &&
                   search(col + 1, 0, next_carry, 0);
        }
        if (used_digit_[needed] || (needed == 0 && model_.is_leading[res_li])) {
            return false;
        }
        used_digit_[needed] = true;
        assigned_[res_li] = needed;
        if (search(col + 1, 0, next_carry, 0)) {
            return true;
        }
        assigned_[res_li] = -1;
        used_digit_[needed] = false;
        return false;
    }

    PuzzleModel const& model_;
    std::array<int, 10> assigned_{};
    std::array<bool, 10> used_digit_{};
};

}  // namespace

std::optional<std::map<char, int>> solve(const std::string& puzzle) {
    PuzzleModel model;
    if (!parse_puzzle(puzzle, model)) {
        return std::nullopt;
    }
    ColumnCarrySolver solver(model);
    if (!solver.solve()) {
        return std::nullopt;
    }
    return solver.build_solution();
}

}  // namespace alphametics
