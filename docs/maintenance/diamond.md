# Diamond (`exercises/practice/diamond`) — File-Role Map & Validation

## Overview

`exercises/practice/diamond/.meta/config.json` declares `solution`, `test`, and `example` entries under `"files"` (no `"editor"` key is present). All paths resolve cleanly inside `exercises/practice/diamond` and match the repository's CMake naming rule (`diamond` -> `diamond_test.cpp`, `diamond.cpp`, `diamond.h`), so `.meta/config.json` required **no changes**.

## Role Map

| Role / Category | Repository Path | Maintained By | Purpose |
| :--- | :--- | :--- | :--- |
| `solution` (stub source) | `exercises/practice/diamond/diamond.cpp` | Track maintainers (unsolved placeholder) | Learner-facing implementation stub (`// TODO: add your solution here`). |
| `solution` (stub header) | `exercises/practice/diamond/diamond.h` | Track maintainers (unsolved placeholder) | Learner-facing header stub. |
| `test` | `exercises/practice/diamond/diamond_test.cpp` | Track maintainers (hand-maintained) | `5` Catch2 `TEST_CASE` blocks tagged with canonical UUIDs matching `.meta/tests.toml`. |
| `example` (reference source) | `exercises/practice/diamond/.meta/example.cpp` | Track maintainers | Reference implementation of `diamond::rows(char)`. |
| `example` (reference header) | `exercises/practice/diamond/.meta/example.h` | Track maintainers | Reference declaration `std::vector<std::string> rows(char middle_letter);`. |
| `editor` | *(not declared in `.meta/config.json`)* | — | No `"editor"` key is configured for `diamond`. |
| Metadata manifest | `exercises/practice/diamond/.meta/config.json` | Track maintainers | Declares `solution`, `test`, and `example` file roles. |
| Canonical test selection | `exercises/practice/diamond/.meta/tests.toml` | `configlet sync` | Tracks the `5` canonical UUID entries (`5` included, `0` excluded). |
| Per-exercise build recipe | `exercises/practice/diamond/CMakeLists.txt` | Track maintainers | Compiles `diamond_test.cpp` + `diamond.cpp` + `diamond.h` + `test/tests-main.cpp` (or `catchlib`). |
| Test harness | `exercises/practice/diamond/test/catch.hpp`, `test/tests-main.cpp` | Track maintainers (Catch2 v2.13.6) | Vendored Catch2 runner used when building standalone. |

## How the Runners Locate `diamond_test.cpp` and `.meta/example.cpp`

1. **Per-exercise CMake (`exercises/practice/diamond/CMakeLists.txt:1-36`):**
   - Extracts `exercise` from the directory name (`diamond`), converts `-` to `_` (`file = diamond`, `line 11`), checks `if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${file}.cpp)` (`lines 14-18`), and compiles `${file}_test.cpp` + `${file}.cpp` + `${file}.h` + `test/tests-main.cpp` (or `$<TARGET_OBJECTS:catchlib>` under root builds).
   - **Why `.meta/example.cpp` isn't compiled directly in-place:** `CMakeLists.txt` only looks for `diamond.cpp` and `diamond.h` in the exercise root, protecting learners from receiving `.meta/example.*` solutions.
2. **Root CI Preparation (`CMakeLists.txt:4-17` `build_fixup`):**
   - Copies `exercises/practice/diamond/` into `build_exercises/practice/diamond/` (`lines 8-9`) and renames `.meta/example.h` -> `diamond.h` (`lines 10-12`) and `.meta/example.cpp` -> `diamond.cpp` (`lines 13-15`) before invoking `add_subdirectory` (`line 25`).

## Maintained vs. Generated Artifacts

- **Maintained (tracked in Git):** all files listed in the role map above (`diamond.cpp`, `diamond.h`, `diamond_test.cpp`, `.meta/example.*`, `.meta/config.json`, `.meta/tests.toml`, `.docs/instructions.md`, `CMakeLists.txt`, `test/*`).
- **Generated (never committed):**
  - Gitignored by `.gitignore`: `build_exercises/`, `CMakeCache.txt`, `CMakeFiles/`, `Makefile`, `cmake_install.cmake`.
  - **Not gitignored:** `build/` (creating `build/` inside the repository working tree would pollute `git status`, so all CMake builds must run inside isolated temporary copies).

## Reproducible Validation Commands

```bash
python3 tools/course_checks/r20-t048.py exercises/practice/diamond
python3 work/R20-T048/check.py
```

Expected final output of `work/R20-T048/check.py`:

```text
RESULT: PASS - executed 5 cases
```
