# Maintenance: resistor-color

## Overview
- Exercise: `exercises/practice/resistor-color`
- Task: R20-T029
- Goal: Isolated runner for `resistor-color` that verifies the reference implementation in a temporary sandbox while preserving unsolved learner starter files and their hashes.

## Tool Requirements
- **C++ Compiler**: C++17 compatible compiler (Clang/GCC/MSVC).
- **Build System**: CMake (>= 3.5.1).
- **Runtime**: Python 3.8+.
- **Test Framework**: Catch2 (included in track or system library).

## Isolated Runner Command

To run the full suite against the reference implementation in an isolated temporary directory:

```bash
python3 tools/course_checks/r20-t029.py
```

### Passing Catch2 Arguments
Optional filters can be passed directly to Catch2:

```bash
# Run specific test case
python3 tools/course_checks/r20-t029.py Black

# List test cases without running
python3 tools/course_checks/r20-t029.py --list-tests
```

## Runner Integrity Guarantees
1. **Isolated Execution**:
   - The exercise directory (including dotfiles) is cloned into a unique temporary directory created via `tempfile.mkdtemp`.
   - `.meta/example.cpp` and `.meta/example.h` are substituted into `resistor_color.cpp` and `resistor_color.h` only inside the temporary directory.
   - The test executable is compiled and executed in that isolated sandbox.
   - The sandbox directory is completely deleted in the `finally` block upon completion.
2. **Learner File Protection**:
   - SHA256 hashes of `exercises/practice/resistor-color/resistor_color.cpp` and `resistor_color.h` are computed prior to execution.
   - Post-execution hashes are verified to be strictly identical to ensure learner stubs remain unsolved and unmodified even in the event of test failure or interruption.
3. **Failure Propagation**:
   - Non-zero compiler or test exit codes are propagated to the caller.
   - Zero-test runs (e.g. from invalid test filters) are caught and reported as non-zero exit failures.
