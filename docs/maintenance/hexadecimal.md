# hexadecimal test maintenance

This document describes the test generation route, maintenance approach, and verification process for `exercises/practice/hexadecimal/`.

## Test Generation Route

The track maintains test definitions and exercise configuration through the following files:

| Role | Path | Maintenance Method |
| --- | --- | --- |
| Exercise Configuration | `exercises/practice/hexadecimal/.meta/config.json` | Maintained metadata file defining solution, test, and reference files. |
| Test Suite | `exercises/practice/hexadecimal/hexadecimal_test.cpp` | Maintained Catch2 C++ test source. Hexadecimal was deprecated in upstream problem specifications in favor of `all-your-base` (Exercism problem-specifications issue #279). No upstream `canonical-data.json` or track-level Jinja template exists for this exercise; test cases are maintained by hand directly in C++. |
| Reference Implementation | `exercises/practice/hexadecimal/.meta/example.cpp` and `example.h` | Reference solution implementing `int convert(const std::string &text)`. Copied to `hexadecimal.cpp` and `hexadecimal.h` only inside isolated test build directories. |

## Generation and Sync Command

From the repository root, configlet checks the canonical metadata and synchronization status:

```sh
./bin/configlet sync --exercise hexadecimal --tests
```

Because `hexadecimal` is deprecated in problem specifications, configlet reports:
```
Checking exercises...
The `hexadecimal` exercise has up-to-date tests!
```
No `.meta/tests.toml` is emitted by upstream problem specifications, and no per-exercise Jinja template exists. The test source is maintained directly in `hexadecimal_test.cpp`.

## Case-to-Output Mapping

The test suite consists of 10 test cases, anchored on three canonical base-conversion cases:

| Test Name | Input (`text`) | Expected Value | Representation | Rationale / Mapping |
| --- | --- | ---: | --- | --- |
| `hex_1_is_decimal_1` | `"1"` | `1` | `0x1` | Single-digit hexadecimal value equals decimal 1. |
| `hex_c_is_decimal_12` | `"c"` | `12` | `0xc` | Lowercase hexadecimal character 'c' corresponds to decimal 12. |
| `hex_10_is_decimal_16` | `"10"` | `16` | `0x10` | Two-digit base-16 place value: $1 \times 16^1 + 0 \times 16^0 = 16$. |
| `hex_af_is_decimal_175` | `"af"` | `175` | `0xaf` | Multiple lowercase alphabetic digits: $10 \times 16 + 15 = 175$. |
| `hex_100_is_decimal_256` | `"100"` | `256` | `0x100` | Power of 16: $1 \times 16^2 = 256$. |
| `hex_19ace_is_decimal_105166` | `"19ace"` | `105166` | `0x19ace` | Multi-digit mixed alphanumeric conversion. |
| `invalid_hex_is_decimal_0` | `"carrot"` | `0` | `0` | Invalid non-hexadecimal characters return 0 as error sentinel. |
| `black` | `"000000"` | `0` | `0x000000` | Hex RGB colour code for black. |
| `white` | `"ffffff"` | `16777215` | `0xffffff` | Hex RGB colour code for white ($16^6 - 1$). |
| `yellow` | `"ffff00"` | `16776960` | `0xffff00` | Hex RGB colour code for yellow. |

## Build and Reproduction Commands

To reproduce the build and execute all test cases locally:

```sh
cmake -S exercises/practice/hexadecimal -B exercises/practice/hexadecimal/build -DEXERCISM_RUN_ALL_TESTS=ON
cmake --build exercises/practice/hexadecimal/build
./exercises/practice/hexadecimal/build/hexadecimal
```

## Automated Verification

The course check validates reproducibility across two independent temporary copies, verifies that the three anchor cases and all remaining test cases pass against the reference solution, and confirms that learner starter files remain unsolved:

```sh
python3 work/R20-T022/check.py
```
