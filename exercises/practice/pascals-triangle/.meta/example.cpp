#include "pascals_triangle.h"

namespace pascals_triangle {

std::vector<std::vector<int>> generate_rows(size_t n) {
    std::vector<std::vector<int>> triangle;

    for (size_t row_index = 0; row_index < n; ++row_index) {
        std::vector<int> current_row;

        // In Pascal's Triangle, the entry at row_index and col_index is C(row_index, col_index).
        // The first element of each row is always 1: C(row_index, 0) = 1.
        int current_cell = 1;
        for (size_t col_index = 0; col_index <= row_index; ++col_index) {
            current_row.push_back(current_cell);
            // Derive the next binomial coefficient using the relation:
            // C(n, k + 1) = C(n, k) * (n - k) / (k + 1)
            current_cell = current_cell * static_cast<int>(row_index - col_index) / static_cast<int>(col_index + 1);
        }

        triangle.push_back(current_row);
    }

    return triangle;
}

}  // namespace pascals_triangle
