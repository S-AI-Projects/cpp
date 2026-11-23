# D&D Character (`exercises/practice/dnd-character`) — Mutation Analysis for `modifier`

## Overview

This note records a deliberate single-expression mutation of `dnd_character::modifier(int score)` in `exercises/practice/dnd-character/.meta/example.cpp` and verifies that the existing Catch2 suite (`18` enabled cases out of `20` entries in `.meta/tests.toml`) rejects it. The maintained reference implementation passes all `18/18` tests and is **not** buggy.

## Reference vs. Mutant Diff

In `exercises/practice/dnd-character/.meta/example.cpp:9-11`:

```diff
-int modifier(int score) {
-    return std::floor((static_cast<double>(score) - 10) / 2);
-}
+int modifier(int score) { return (score - 10) / 2; }
```

- **Mutant file:** `work/R20-T043/mutant.cpp`
- **Semantic change:** Replaces floating-point division + `std::floor` (rounds toward $-\infty$) with signed integer division `(score - 10) / 2` (in C++17, integer division truncates toward `0`).

## Rejecting Test Cases (`dnd_character_test.cpp`)

Running the test executable against `work/R20-T043/mutant.cpp` passes `14` cases and fails **`4`** existing cases (every odd score below `10`):

| Canonical UUID | Catch2 Test Case Name | Lines in `dnd_character_test.cpp` | Input (`score`) | Expected (`reference`) | Mutant Output |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `1e9ae1dc-35bd-43ba-aa08-e4b94c20fa37` | `"ability modifier for score 3 is -4"` | `29-32` | `3` | `-4` | **`-3`** |
| `5b519fcd-6946-41ee-91fe-34b4f9808326` | `"ability modifier for score 5 is -3"` | `41-44` | `5` | `-3` | **`-2`** |
| `099440f5-0d66-4b1a-8a10-8f3a03cc499f` | `"ability modifier for score 7 is -2"` | `51-54` | `7` | `-2` | **`-1`** |
| `c70f0507-fa7e-4228-8463-858bfbba1754` | `"ability modifier for score 9 is -1"` | `61-64` | `9` | `-1` | **`0`** |

- **Smallest rejecting input in the specification domain (`3..18`):** **`score = 3`**, covered by the first (unguarded) test case `"ability modifier for score 3 is -4"` (`1e9ae1dc-35bd-43ba-aa08-e4b94c20fa37`).

## Original vs. Mutant Output Across the Valid Domain (`3..18`)

| Score | `score - 10` | Reference (`std::floor`) | Mutant (`(score - 10) / 2`) | Outcome |
| :---: | :---: | :---: | :---: | :---: |
| `3` | `-7` | `-4` | `-3` | **FAIL** (minimal rejecting input) |
| `4` | `-6` | `-3` | `-3` | pass |
| `5` | `-5` | `-3` | `-2` | **FAIL** |
| `6` | `-4` | `-2` | `-2` | pass |
| `7` | `-3` | `-2` | `-1` | **FAIL** |
| `8` | `-2` | `-1` | `-1` | pass |
| `9` | `-1` | `-1` | `0` | **FAIL** |
| `10` | `0` | `0` | `0` | pass |
| `11` | `1` | `0` | `0` | pass |
| `12` | `2` | `1` | `1` | pass |
| `13` | `3` | `1` | `1` | pass |
| `14` | `4` | `2` | `2` | pass |
| `15` | `5` | `2` | `2` | pass |
| `16` | `6` | `3` | `3` | pass |
| `17` | `7` | `3` | `3` | pass |
| `18` | `8` | `4` | `4` | pass |

*(Note: `"random character is valid"` compares `character.hitpoints == 10 + dnd_character::modifier(character.constitution)`, where `Character::Character()` in `.meta/example.h:15` calls the same `modifier` implementation, so it does not detect the mutant independently; the dedicated `ability modifier for score ...` tests catch all four odd-negative discrepancies.)*

## Verification Command

```bash
python3 work/R20-T043/check.py
```

Expected final output line:

```text
RESULT: PASS - executed 18 cases
```
