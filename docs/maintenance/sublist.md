# sublist reference implementation refactoring

This document notes the scoped readability refactoring of `is_sublist` in `exercises/practice/sublist/.meta/example.cpp`.

## Context and Readability Improvement

The prior implementation of `is_sublist` used complex iterator arithmetic to create a boundary iterator and iterated manually using `std::advance` and `std::equal`:

```cpp
// Prior implementation:
bool is_sublist(const std::vector<int>& sublist,
                const std::vector<int>& superlist) {
    auto superlist_end = std::prev(
        superlist.end(), std::max<std::size_t>(1, sublist.size()) - 1);
    for (auto it{superlist.begin()}; it != superlist_end; std::advance(it, 1)) {
        if (std::equal(sublist.begin(), sublist.end(), it)) return true;
    }
    return false;
}
```

This structure suffered from several readability issues:
1. Calculating `superlist_end` via `std::prev` with `std::max<std::size_t>(1, sublist.size()) - 1` obscures the termination bound.
2. Manual iteration with `std::advance` and `std::equal` reinvents sequence matching.

### Refactored Implementation

The refactored function replaces manual looping with the standard library algorithm `std::search`:

```cpp
bool is_sublist(const std::vector<int>& sublist,
                const std::vector<int>& superlist) {
    // Invariant: An empty list is trivially a contiguous sublist of any list.
    // std::search finds the first contiguous occurrence of sublist within superlist.
    return std::search(superlist.begin(), superlist.end(),
                       sublist.begin(), sublist.end()) != superlist.end();
}
```

### Invariant and Behavior Preservation

- **Invariant**: Any list (including an empty list) is a contiguous sublist of a larger or equal list. `std::search` returns `superlist.begin()` when `sublist` is empty, indicating a match.
- **Contract**: Preserves the exact signature `bool is_sublist(const std::vector<int>&, const std::vector<int>&)` and enum return values for `sublist(...)`.
- **Baseline Cases**:
  - `empty lists` (`sublist({}, {})` -> `List_comparison::equal`)
  - `empty list within non empty list` (`sublist({}, {1, 2, 3})` -> `List_comparison::sublist`)
  - `non empty list contains empty list` (`sublist({1, 2, 3}, {})` -> `List_comparison::superlist`)

All 18 test cases produce identical results before and after refactoring.
