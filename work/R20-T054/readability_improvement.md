# Readability Improvement: Pascal's Triangle Example Solution

## Overview
This document outlines the readability improvements applied to `exercises/practice/pascals-triangle/.meta/example.cpp`. The goal of the refactoring is to enhance clarity for learners by replacing terse, single-letter variables with descriptive names and explicitly documenting the recurrence relation used in cell calculations while preserving the exact public API, ordering, and return types.

---

## Before-and-After Diff

```diff
--- a/exercises/practice/pascals-triangle/.meta/example.cpp
+++ b/exercises/practice/pascals-triangle/.meta/example.cpp
@@ -3,21 +3,25 @@
 namespace pascals_triangle {
 
 std::vector<std::vector<int>> generate_rows(size_t n) {
-    std::vector<std::vector<int>> res;
+    std::vector<std::vector<int>> triangle;
 
-    for (size_t i = 0; i < n; i++) {
-        std::vector<int> rowNum;
+    for (size_t row_index = 0; row_index < n; ++row_index) {
+        std::vector<int> current_row;
 
-        int val = 1;
-        for (size_t k = 0; k <= i; k++) {
-            rowNum.push_back(val);
-            val = val * (i - k) / (k + 1);
+        // In Pascal's Triangle, the entry at row_index and col_index is C(row_index, col_index).
+        // The first element of each row is always 1: C(row_index, 0) = 1.
+        int current_cell = 1;
+        for (size_t col_index = 0; col_index <= row_index; ++col_index) {
+            current_row.push_back(current_cell);
+            // Derive the next binomial coefficient using the relation:
+            // C(n, k + 1) = C(n, k) * (n - k) / (k + 1)
+            current_cell = current_cell * static_cast<int>(row_index - col_index) / static_cast<int>(col_index + 1);
         }
 
-        res.push_back(rowNum);
+        triangle.push_back(current_row);
     }
 
-    return res;
+    return triangle;
 }
 
 }  // namespace pascals_triangle
```

---

## Why This Concrete Readability Improvement Helps Learners

1. **Clarifies 2D Coordinate Mental Models**:
   - In the original code, the nested loops used `i` and `k`, while the accumulator vector was named `rowNum`.
   - Naming `rowNum` was confusing because it represented an entire row vector, yet the name implied a single scalar number (like "row number").
   - Changing `res -> triangle`, `rowNum -> current_row`, `i -> row_index`, and `k -> col_index` maps directly to standard 2D grid terminology `(row_index, col_index)`, making it immediately clear how the triangle rows and columns are constructed.

2. **Demystifies the Binomial Recurrence Formula**:
   - The original formula `val = val * (i - k) / (k + 1);` appears cryptic to someone seeing it for the first time without context. Learners often struggle to connect that expression with Pascal's Triangle (which is typically introduced via the addition rule $C(n, k) = C(n-1, k-1) + C(n-1, k)$).
   - By naming `val -> current_cell` and adding an explanatory comment describing the multiplicative recurrence for combinations:
     $$\binom{n}{k+1} = \binom{n}{k} \times \frac{n - k}{k + 1}$$
     learners can immediately understand *why* the values update without needing to recompute the entire previous row or deal with full factorial division.

3. **Prevents Signed vs. Unsigned Conversion Confusion**:
   - The loop indices `row_index` and `col_index` are `size_t` (unsigned), whereas the cell value is `int`. Explicit `static_cast<int>` in the arithmetic clarifies type transitions and avoids implicit conversion surprises.

4. **Preserves Exact Behavior and API**:
   - The function signature `std::vector<std::vector<int>> generate_rows(size_t n)` and namespace `pascals_triangle` remain unchanged.
   - The row ordering, element ordering, and time/space complexity are strictly preserved.
