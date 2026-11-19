# High Scores Maintenance Documentation

## Overview

This document details the isolated test execution architecture for `exercises/practice/high-scores`. The isolated runner ensures that learner-facing files (`high_scores.cpp`, `high_scores.h`) remain strictly untouched and unsolved, while executing full verification tests against the maintained reference implementation.

## Tool Requirements and Prerequisites

- **C++ Compiler**: C++17 compliant compiler (`clang++` or `g++`).
- **Build System**: CMake (>= 3.5.1) and Make.
- **Python Runtime**: Python 3.8+ with standard library modules (`hashlib`, `json`, `shutil`, `subprocess`, `tempfile`).

## Execution Command

The test runner is located at `tools/course_checks/r20-t009.py` and can be invoked directly or via the verification wrapper:

```bash
python3 tools/course_checks/r20-t009.py
# or
python3 work/R20-T009/check.py
```

## Isolation Architecture & Guarantees

1. **Working Tree Immutability**:
   The working tree (`exercises/practice/high-scores/`) is never modified during execution. SHA-256 hashes of learner stubs are calculated immediately prior to execution and checked after completion (even on errors or interrupted runs).
2. **Dynamic Scratch Environment**:
   A dedicated temporary directory is created for each run using `tempfile.mkdtemp()`. The exercise files and directory structure are copied into the scratch workspace, where reference solutions (`.meta/example.cpp` and `.meta/example.h`) are substituted.
3. **Execution Modes**:
   The runner evaluates three distinct execution scenarios:
   - **Real Reference**: Builds and executes the canonical reference solution, verifying that all test cases pass (including anchor cases `List of scores`, `Latest score`, and `Personal best`).
   - **Failing Reference**: Intentionally introduces a logic fault into the reference to verify that Catch2 and the runner accurately catch assertions and exit with a non-zero code.
   - **Zero Test Selection**: Verifies that a test run producing zero executed test cases triggers a failure condition.
4. **Cleanup Guarantee**:
   All temporary directories and build artifacts are cleaned up using `try ... finally` blocks.
