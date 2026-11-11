# ISBN Verifier Exercise Maintenance

This document provides the test runner information for `exercises/practice/isbn-verifier/`.

## File Roles

All paths are relative to `exercises/practice/isbn-verifier/`.

| Role | Path | Status |
|------|------|--------|
| Solution stub | `isbn_verifier.cpp` | Empty stub (learner file) |
| Solution stub | `isbn_verifier.h` | Empty stub (learner file) |
| Test file | `isbn_verifier_test.cpp` | Hand-maintained tests |
| Reference | `.meta/example.cpp` | Reference implementation |
| Reference | `.meta/example.h` | Reference header |
| Config | `.meta/config.json` | Exercise metadata |

## Isolated Test Runner

The exercise uses a specialized test runner in `tools/course_checks/r20-t039.py` that:

1. Parses `exercises/practice/isbn-verifier/.meta/config.json` to find file paths
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
    "solution": ["isbn_verifier.cpp", "isbn_verifier.h"],
    "test": ["isbn_verifier_test.cpp"],
    "example": [".meta/example.cpp", ".meta/example.h"]
  }
}
```

## How Tests Are Found

The tests are found via CMake, which:
1. Reads `CMakeLists.txt` in the exercise directory
2. Compiles `isbn_verifier_test.cpp` with the implementation
3. Links against the build configuration

## Usage

```bash
# Validate with reference implementation
python3 work/R20-T039/check.py

# Or use the standalone runner
python3 tools/course_checks/r20-t039.py
```

## Verified Test Cases (19 total)

Named cases that must pass:
- `valid_isbn`
- `invalid_isbn_check_digit`
- `valid_isbn_with_a_check_digit_of_10`

All other enabled cases: 16 additional tests