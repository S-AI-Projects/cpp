# Knapsack (`exercises/practice/knapsack`) — Canonical Case & Maintenance Notes

## Overview

The `knapsack` practice exercise tracks 8 canonical cases in `exercises/practice/knapsack/.meta/tests.toml` from upstream `problem-specifications` (`exercises/knapsack/canonical-data.json`):

- **Counts before maintenance update:** `8` total / `7` included / `1` excluded
- **Counts after maintenance update:** `8` total / `7` included / `1` excluded (`include` and `reimplements` values unchanged)
- **Test generator:** `exercises/practice/knapsack/.meta/create_tests.py` reads `.meta/tests.toml` and `canonical-data.json`. When formatted with `clang-format` v18.1.2 using the repository `.clang-format`, its output is byte-identical to `exercises/practice/knapsack/knapsack_test.cpp` (`0` diff lines).

## Why `comment = "..."` Keys Are Used in `tests.toml`

As documented in `exercises/practice/knapsack/.meta/tests.toml:1-10`, `configlet sync` regenerates `tests.toml` and strips `#` line comments, while preserving custom key/value pairs on each `[<uuid>]` table. All per-case maintenance rationales must therefore be recorded using `comment = "..."` keys rather than `#` comments.

## Rationale for Excluded UUID `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7`

- **Classification:** **Replacement case** (not an unsupported C++ feature and not a bug in the C++ track or reference solution).
- **Upstream canonical history:** In `problem-specifications/exercises/knapsack/canonical-data.json`, UUID `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` (`"no items"`) encoded `input.items` as an empty JSON object (`"items": {}`) instead of an empty JSON array (`"items": []`). Upstream introduced UUID `3993a824-c20e-493d-b3c9-ee8a7753ee59` (`"no items"`) with `"reimplements": "a4d7d2f0-ad8a-460c-86f3-88ba709d41a7"` and `"items": []`.
- **C++ test suite impact:** `3993a824-c20e-493d-b3c9-ee8a7753ee59` is included and generates `TEST_CASE("no items", "[maximumValue][3993a824-c20e-493d-b3c9-ee8a7753ee59]")` at `exercises/practice/knapsack/knapsack_test.cpp:10-14`. Keeping `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` at `include = false` prevents `.meta/create_tests.py` from emitting two `TEST_CASE("no items", ...)` blocks with identical names, which Catch2 v2.13.6 rejects as duplicate test case names.

## Reference Implementation Summary (`exercises/practice/knapsack/.meta/example.cpp:5-12`)

`int maximum_value(int maximum_weight, const std::vector<Item>& items)` implements 0/1 knapsack dynamic programming in $O(|items| \cdot \text{maximum\_weight})$ time and $O(\text{maximum\_weight})$ space:

1. `std::vector<int> dp(maximum_weight + 1);` (`example.cpp:6`) zero-initializes best values for capacities `0..maximum_weight`.
2. `for (auto item : items)` (`example.cpp:7`) visits each item once.
3. `for (int weight = maximum_weight; weight >= item.weight; --weight)` (`example.cpp:8`) iterates capacity in reverse so each item is transitioned at most once (0/1 constraint) and skips items where `item.weight > maximum_weight`.
4. `dp[weight] = std::max(dp[weight], dp[weight - item.weight] + item.value);` (`example.cpp:9-10`) chooses the better of excluding or including `item` at capacity `weight`.
5. `return dp[maximum_weight];` (`example.cpp:11`) returns the optimal value for `maximum_weight`.

## Canonical Case Mapping Table

| UUID | Description | Included? | Reimplements | Test Name in `knapsack_test.cpp` | Test Lines | Input (`max_weight`, `items`) | Expected | Reference C++ Operation (`example.cpp`) | Rationale |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` | `"no items"` | `false` | — | *(superseded by `3993a824-c20e-493d-b3c9-ee8a7753ee59`)* | — | `100`, `items: {}` (JSON object in canonical data) | `0` | Covered via `3993a824`: `std::vector<int> dp(101)` zero-init (`example.cpp:6`), outer loop skipped (`example.cpp:7`), `return dp[100]` (`example.cpp:11`). | **Replacement case**: excluded because upstream reimplemented `"items": {}` as `"items": []` in `3993a824-c20e-493d-b3c9-ee8a7753ee59`; excluding avoids duplicate Catch2 `TEST_CASE("no items")`. |
| `3993a824-c20e-493d-b3c9-ee8a7753ee59` | `"no items"` | `true` | `a4d7d2f0-ad8a-460c-86f3-88ba709d41a7` | `"no items"` | `10-14` | `100`, `items = {}` (`std::vector<Item>{}`) | `0` | `std::vector<int> dp(101)` value-initializes all entries to `0` (`example.cpp:6`); `for (auto item : items)` executes 0 iterations (`example.cpp:7`); returns `dp[100] == 0` (`example.cpp:11`). | **Named case 1 & replacement case**: verifies empty `std::vector<Item>` base contract with capacity `100`. |
| `1d39e98c-6249-4a8b-912f-87cb12e506b0` | `"one item, too heavy"` | `true` | — | `"one item, too heavy"` | `18-23` | `10`, `items = {{100, 1}}` | `0` | Outer loop visits `{100, 1}` (`example.cpp:7`); inner loop guard `weight >= item.weight` (`10 >= 100`, `example.cpp:8`) is immediately `false`; returns `dp[10] == 0` (`example.cpp:11`). | **Named case 2**: verifies capacity boundary guard when a single item's weight exceeds `maximum_weight`. |
| `833ea310-6323-44f2-9d27-a278740ffbd8` | `"five items (cannot be greedy by weight)"` | `true` | — | `"five items (cannot be greedy by weight)"` | `25-31` | `10`, `items = {{2, 5}, {2, 5}, {2, 5}, {2, 5}, {10, 21}}` | `21` | Four `{2, 5}` items fill `dp[8] = 20, dp[10] = 20`; fifth item `{10, 21}` updates `dp[10] = std::max(dp[10], dp[0] + 21) = std::max(20, 21) = 21` (`example.cpp:8-10`). | **Named case 3**: refutes greedy lightest-first selection (`20`) in favor of exact 0/1 DP transition (`21`). |
| `277cdc52-f835-4c7d-872b-bff17bab2456` | `"five items (cannot be greedy by value)"` | `true` | — | `"five items (cannot be greedy by value)"` | `33-39` | `10`, `items = {{2, 20}, {2, 20}, {2, 20}, {2, 20}, {10, 50}}` | `80` | Four `{2, 20}` items produce `dp[8] = 80, dp[10] = 80`; fifth item `{10, 50}` evaluates `std::max(80, dp[0] + 50) = 80` (`example.cpp:8-10`). | Refutes greedy highest-single-value selection (`50`) in favor of combining four lighter items (`80`). |
| `81d8e679-442b-4f7a-8a59-7278083916c9` | `"example knapsack"` | `true` | — | `"example knapsack"` | `41-46` | `10`, `items = {{5, 10}, {4, 40}, {6, 30}, {4, 50}}` | `90` | Reverse DP transition combines `{4, 40}` and `{4, 50}` at `weight = 8..10` via `dp[weight - 4] + 50 = 90` (`example.cpp:8-10`). | Verifies the worked example from `.docs/instructions.md:12-25`. |
| `f23a2449-d67c-4c26-bf3e-cde020f27ecc` | `"8 items"` | `true` | — | `"8 items"` | `48-54` | `104`, `8` items (`{25,350}, {35,400}, {45,450}, ...`) | `900` | Reverse 1D DP over `dp` of size `105` combines `{25, 350}`, `{35, 400}`, `{25, 70}`, `{5, 20}`, `{2, 5}`, `{2, 5}` (or `{25, 350} + {45, 450} + {25, 70} + {5, 20} + {2, 5} + {2, 5} = 900` at weight `104`). | Verifies multi-item combination across capacity `104`. |
| `7c682ae9-c385-4241-a197-d2fa02c81a11` | `"15 items"` | `true` | — | `"15 items"` | `56-63` | `750`, `15` items (weights `70..120`, values `135..240`) | `1458` | Reverse 1D DP over `dp` of size `751` evaluates all 15 items without 0/1 reuse and returns `dp[750] == 1458` (`example.cpp:6-11`). | Verifies larger capacity table (`751` ints) and 15-item subset selection. |

## Verification Command

Run from the repository root:

```bash
python3 work/R20-T041/check.py
```

Expected final output line:

```text
RESULT: PASS - executed 7 cases
```
