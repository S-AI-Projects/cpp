# Roman Numerals Exercise Maintenance

This document provides maintenance notes for the reference implementation refactor in `exercises/practice/roman-numerals/`.

## Refactor Summary

**File changed:** `exercises/practice/roman-numerals/.meta/example.cpp`

### Before (Original)
- Used confusing method names: `place()`, `place_numeral()`, `place_numeral_penultimate()`
- Magic indices (0, 1, 2, 4, 6) with unclear relationships
- Subtractive notation logic was hard to follow
- `thousands()`, `hundreds()`, `tens()`, `ones()` each called `place()` with different indices

### After (Refactored)
- **Single coherent method**: `process_place(PlaceConfig)` handles all decimal places uniformly
- **Explicit configuration**: `PlaceConfig` struct documents the numeral relationships for each decimal place (unit/half/ten)
- **Clear subtractive notation order**: Unit numeral comes BEFORE half/ten (e.g., "IV" not "VI", "IX" not "XI")
- **Self-documenting code**: Comments explain 9x, 5x, 4x, 1x-3x handling per place
- **No magic numbers**: All indices are in the `PLACES` array with clear labels

### Readability Improvement
The refactor replaces 6 private methods with 1 method + explicit configuration, making the Roman numeral generation algorithm immediately understandable:
1. Try 9x (unit before ten)
2. Try 5x (half numeral)
3. Try 4x (unit before half)
4. Add 1x-3x (repeat unit)

### Behavioral Baseline (Named Cases)
All named cases pass:
- `1_is_i` → "I"
- `2_is_ii` → "II"  
- `3_is_iii` → "III"
- All 27 test cases pass identically

## Automated Check

Run the check:
```bash
python3 work/R20-T034/check.py
```