# Maintenance Guide: Crypto Square

This document provides maintenance and architectural details for the `crypto-square` practice exercise in the Exercism C++ track.

---

## 1. Structure of `.meta/config.json`

The file `exercises/practice/crypto-square/.meta/config.json` is the authoritative metadata descriptor used by Exercism tooling (such as `configlet`, the Exercism CLI, and automated test runners).

In this exercise, the `files` object declares the following mappings:

```json
"files": {
  "solution": [
    "crypto_square.cpp",
    "crypto_square.h"
  ],
  "test": [
    "crypto_square_test.cpp"
  ],
  "example": [
    ".meta/example.cpp",
    ".meta/example.h"
  ]
}
```

### File Categories & Keys

- **`files.solution`**:
  Lists the files that learners edit and submit to pass the exercise.
  - Paths: `crypto_square.cpp`, `crypto_square.h`
  - In stubs provided to learners, these files contain basic function/class templates or empty declarations.
  - When learners submit solutions via `exercism submit`, only files listed under `files.solution` are transferred to the platform.

- **`files.test`**:
  Lists the test suite files that verify a learner's implementation against the exercise specification.
  - Paths: `crypto_square_test.cpp`
  - These tests run against both the learner's implementation and the reference example solution during CI/automated verification.

- **`files.example`**:
  Lists the reference implementation used to verify track integrity and validate that the test suite passes.
  - Paths: `.meta/example.cpp`, `.meta/example.h`
  - Automated CI pipelines (and track test tooling) substitute the files in `files.example` into place to ensure the exercise builds and all tests succeed.

- **`files.editor`**:
  An optional array specifying any auxiliary files that should be exposed to the user in the Exercism in-browser code editor (such as extra header files or configuration).
  - In `crypto-square`, `files.editor` is not declared (omitted), meaning only the files specified in `files.solution` are displayed for editing in the browser UI.

---

## 2. Explicit Path Inventory

| Category | File Paths | Purpose |
| :--- | :--- | :--- |
| **Learner Stubs** | `exercises/practice/crypto-square/crypto_square.cpp`<br>`exercises/practice/crypto-square/crypto_square.h` | Initial starter code downloaded by learners; edited and submitted. |
| **Reference Solution** | `exercises/practice/crypto-square/.meta/example.cpp`<br>`exercises/practice/crypto-square/.meta/example.h` | Complete, canonical reference solution used for track validation. |
| **Test Suite** | `exercises/practice/crypto-square/crypto_square_test.cpp` | Catch-based test suite asserting correctness and adherence to canonical tests. |
| **Editor Files** | *None declared* | No `files.editor` entry is present in `config.json`. |
| **Build Configuration** | `exercises/practice/crypto-square/CMakeLists.txt` | CMake build configuration for building and running tests. |
| **Exercise Metadata** | `exercises/practice/crypto-square/.meta/config.json`<br>`exercises/practice/crypto-square/.meta/tests.toml` | Track metadata and canonical test case tracking. |
| **Documentation** | `exercises/practice/crypto-square/.docs/instructions.md` | Problem description and encoding specification. |

---

## 3. Resolution Without Heuristic Filename Searching

Exercism's automated test runners and CI tooling do **not** rely on heuristic searching or wildcard file globbing (e.g., guessing filenames matching `*_test.cpp` or looking for random `.cpp` files in the directory).

Instead, resolution proceeds deterministically via `.meta/config.json`:

1. **Deterministic Manifest Reading**:
   Tooling parses `exercises/practice/crypto-square/.meta/config.json` directly to retrieve explicit path definitions under `files`.
2. **Deterministic Test Execution**:
   - The test runner reads `files.test` to know exactly that `crypto_square_test.cpp` is the test source file.
   - For learner submissions, the test runner reads `files.solution` to know that `crypto_square.cpp` and `crypto_square.h` are the target solution files.
3. **Reference Solution Validation**:
   - To test the reference solution, tooling reads `files.example` (`.meta/example.cpp`, `.meta/example.h`) and `files.solution` (`crypto_square.cpp`, `crypto_square.h`).
   - It renames or copies the example files to the solution paths:
     - `.meta/example.cpp` $\rightarrow$ `crypto_square.cpp`
     - `.meta/example.h` $\rightarrow$ `crypto_square.h`
   - It then invokes CMake (with `-DEXERCISM_RUN_ALL_TESTS=ON`) to compile and execute the test runner.
4. **Header and Translation Unit Alignment**:
   Because `crypto_square_test.cpp` explicitly includes `"crypto_square.h"`, the example header must provide the exact type and method signatures expected by the test file (e.g. `crypto_square::cipher`). Because file mapping is declared explicitly in `config.json`, the build system and test runner never guess or scan arbitrarily across the filesystem.

---

## 4. Tracked Static Files vs. Generated Build Artifacts

To maintain a clean repository and ensure reproducible builds, static exercise sources and generated build artifacts must remain strictly segregated.

### Tracked Static Files (Version Controlled)
These files represent the exercise definition and source code and are committed to Git:
- `CMakeLists.txt`: Defines the build targets (`crypto-square` and `test_crypto-square`).
- `crypto_square.cpp`, `crypto_square.h`: Starter template files for the learner.
- `crypto_square_test.cpp`: Test cases.
- `test/catch.hpp`, `test/tests-main.cpp`: Test framework dependencies (Catch).
- `.meta/config.json`: File registry and track metadata.
- `.meta/example.cpp`, `.meta/example.h`: Reference implementation.
- `.meta/tests.toml`: Status of problem-specifications canonical test cases.
- `.meta/maintenance.md`: Maintenance documentation.
- `.docs/instructions.md`: Problem instructions.

### Generated Build & Test Artifacts (Ignored / Untracked)
When compiling and executing tests locally or in test runners, CMake and the compiler produce transient build artifacts that must **never** be committed to version control:
- **Build Directory**: `build/` (or any configured binary build folder).
- **CMake Cache & Internal Files**:
  - `build/CMakeCache.txt`
  - `build/CMakeFiles/`
  - `build/cmake_install.cmake`
  - `build/Makefile` or `build/*.ninja`
- **Compiled Object Files**:
  - `*.o` / `*.obj` (e.g., `build/CMakeFiles/crypto-square.dir/crypto_square.cpp.o`, `build/CMakeFiles/crypto-square.dir/crypto_square_test.cpp.o`)
- **Compiled Test Executable**:
  - `build/crypto-square` (the final binary linked by CMake, executed by the custom `test_crypto-square` target)
- **Symbol / Debug Files**:
  - `*.dSYM/`, `*.pdb`, `*.idb`
