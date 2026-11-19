# Protein Translation Maintenance Documentation

## Overview

This document provides a comprehensive inventory and role-classification mapping for every file in `exercises/practice/protein-translation`, along with maintenance policies and reproducible validation instructions.

## File-Role Inventory Map

| File Path | Role Classification | Maintenance Policy | Purpose |
|---|---|---|---|
| `protein_translation.cpp` | Learner-facing (Solution Stub) | Editable by learner only | Initial implementation stub providing placeholder definitions for learners. Must remain unsolved in repository. |
| `protein_translation.h` | Learner-facing (Solution Header) | Editable by learner only | Function prototypes and namespace declarations exposed to the learner. |
| `protein_translation_test.cpp` | Track-Maintained (Test Suite) | Maintained by track | Catch2 test cases corresponding to canonical problem specifications. Uses Catch2 macros (`TEST_CASE`, `REQUIRE`). |
| `CMakeLists.txt` | Track-Maintained (Build Script) | Maintained by track | CMake configuration defining targets, C++ standard (C++17), and compiler flags. |
| `test/catch.hpp` | Vendored Dependency | Frozen / Track-Maintained | Single-header Catch2 v2 test framework header. |
| `test/tests-main.cpp` | Track-Maintained (Test Entry) | Maintained by track | Generates `main()` for Catch2 via `#define CATCH_CONFIG_MAIN`. |
| `.meta/config.json` | Exercise Metadata | Maintained by track | JSON manifest defining file roles (`solution`, `test`, `example`), authors, and exercise metadata. |
| `.meta/example.cpp` | Reference Solution (Source) | Maintained by track | Fully implemented canonical reference solution used for track test verification and CI. |
| `.meta/example.h` | Reference Solution (Header) | Maintained by track | Header declarations for the reference solution. |
| `.meta/tests.toml` | Canonical Metadata (Generated/Synced) | Synced via `configlet` | TOML tracking canonical test cases, descriptions, and include/exclude flags from problem-specifications. |
| `.docs/instructions.md` | Problem Description (Synced) | Synced via `configlet` | Problem statement and instructions presented to the learner. |

## Validation Command

To validate that the reference solution passes all canonical test cases:

```bash
# In an isolated temporary copy:
cmake -S exercises/practice/protein-translation -B build -DEXERCISM_RUN_ALL_TESTS=ON
cmake --build build
./build/protein-translation
```

## Configuration Verification

All paths listed in `.meta/config.json`:
- `files.solution`: `["protein_translation.cpp", "protein_translation.h"]` (Matches actual files on disk)
- `files.test`: `["protein_translation_test.cpp"]` (Matches actual test file on disk)
- `files.example`: `[".meta/example.cpp", ".meta/example.h"]` (Matches actual example files on disk)

No configuration drift was detected; `config.json` is accurate.
