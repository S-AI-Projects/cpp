# Eliud's Eggs Exercise Maintenance

This document provides the test runner information for `exercises/practice/eliuds-eggs/`.

## File Roles

All paths are relative to `exercises/practice/eliuds-eggs/`.

| Role | Path | Status |
|------|------|--------|
| Solution stub | `eliuds_eggs.cpp` | Empty stub (learner file) |
| Solution stub | `eliuds_eggs.h` | Empty stub (learner file) |
| Test file | `eliuds_eggs_test.cpp` | Hand-maintained tests |
| Reference | `.meta/example.cpp` | Reference implementation |
| Reference | `.meta/example.h` | Reference header |
| Config | `.meta/config.json` | Exercise metadata |

## Isolated Test Runner

The exercise uses a specialized test runner in `work/R20-T040/check.py` that:

1. Parses `exercises/practice/eliuds-eggs/.meta/config.json` to find file paths
2. Creates a temporary copy of the exercise
3. Substitutes only the reference implementation
4. Builds and runs tests
5. Verifies learner files are unchanged (hash comparison)
6. Cleans up temporary files

## Configuration

From `.meta/config.json`:
```json
{
  "files": {
    "solution": ["eliuds_eggs.cpp", "eliuds_eggs.h"],
    "test": ["eliuds_eggs_test.cpp"],
    "example": [".meta/example.cpp", ".meta/example.h"]
  }
}
```

## How Tests Are Found

The tests are found via CMake, which:
1. Reads `CMakeLists.txt` in the exercise directory
2. Compiles `eliuds_eggs_test.cpp` with the implementation
3. Links against the build configuration

## Usage

```bash
# Validate with reference implementation
python3 work/R20-T040/check.py
```

## Verified Test Cases (4 total)

Named cases that must pass:
- `0 eggs` (input: 0, expected: 0)
- `1 egg` (input: 16, expected: 1)
- `4 eggs` (input: 89, expected: 4)
- `13 eggs` (input: 2000000000, expected: 13)

## Contract Examples

The task R20-T040 adds contract examples documentation in `exercises/practice/eliuds-eggs/.docs/hints.md` covering:
- How 0 eggs maps to binary 0 (0 bits set)
- How 1 egg maps to binary 10000 (1 bit set at position 4)
- How 4 eggs maps to binary 1011001 (4 bits set)

The exercise counts 1-bits (population count) in the binary representation. The specification is clear about what constitutes valid behavior - there are no hidden edge cases beyond what the tests cover.