# R20-T048 Study Notes — `diamond` File Map & Metadata Validator

## 1. Inspected Files

- `exercises/practice/diamond/.docs/instructions.md` (lines 1–52): Generates symmetric letter diamond rows from `'A'` up to supplied letter and back to `'A'`.
- `exercises/practice/diamond/.meta/config.json` (lines 1–21):
  - `files.solution`: `["diamond.cpp", "diamond.h"]`
  - `files.test`: `["diamond_test.cpp"]`
  - `files.example`: `[".meta/example.cpp", ".meta/example.h"]`
  - No `"editor"` key is declared.
  - All 5 declared files exist inside `exercises/practice/diamond` and agree with `CMakeLists.txt` (`diamond` -> `diamond_test.cpp`, `diamond.cpp`, `diamond.h`), so `.meta/config.json` does NOT need modification.
- `exercises/practice/diamond/CMakeLists.txt` (lines 1–67) & root `CMakeLists.txt` (lines 4–27):
  - Per-exercise CMake derives `<file> = diamond` from folder name; root `build_fixup()` copies into `build_exercises/practice/diamond/` and renames `.meta/example.*` -> `diamond.*`.
- `exercises/practice/diamond/.meta/tests.toml` (`5` entries, all included) & `diamond_test.cpp` (`5` `TEST_CASE`s, all tagged `[uuid]`):
  - Anchor cases:
    1. `"Degenerate case with a single 'A' row"` (`202fb4cc-6a38-4883-9193-a29d5cb92076`, `diamond_test.cpp:26-30`)
    2. `"Degenerate case with no row containing 3 distinct groups of spaces"` (`bd6a6d78-9302-42e9-8f60-ac1461e9abae`, `diamond_test.cpp:32-36`)
    3. `"Smallest non-degenerate case with odd diamond side length"` (`af8efb49-14ed-447f-8944-4cc59ce3fd76`, `diamond_test.cpp:38-43`)

## 2. Issue #49 Typo Resolved

- Issue #49 "Done when" truncates the first named case to `"Degenerate case with a single ;"`. The real test name in `diamond_test.cpp:26` and `.meta/tests.toml:13` is `"Degenerate case with a single 'A' row"`.
