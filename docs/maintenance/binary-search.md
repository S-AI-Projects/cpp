# Binary-search file map

## Files declared in `.meta/config.json`

| Role | Config path | Purpose |
|---|---|---|
| `solution` | `binary_search.cpp`, `binary_search.h` | Learner implementation files. |
| `test` | `binary_search_test.cpp` | C++ test source; its header identifies canonical test data version 1.3.0. |
| `example` | `.meta/example.cpp`, `.meta/example.h` | Maintained reference implementation and interface. Course checks copy these to the configured solution paths in a temporary exercise copy. |
| `editor` | Not declared | This exercise has no editor-specific file entries. The path checker validates this role if a future config adds it. |

The paths are relative to `exercises/practice/binary-search`, the directory containing this config. The reusable checker reads the `files` object, resolves each declared path under that exercise directory, rejects absolute paths and `..` traversal, and checks that each target is a file:

```sh
python3 tools/course_checks/r20-t018.py
```

## How the CMake runner finds the test

The exercise `CMakeLists.txt` takes the current directory name (`binary-search`), changes hyphens to underscores (`binary_search`), and adds `binary_search_test.cpp` to the executable. The config's `test` entry names that same maintained test source for track tooling. The `.meta/example.cpp` reference is not selected by CMake directly; a reference-validation runner copies it to the `solution` path in an isolated copy before configuring and building.

`binary_search_test.cpp` is the checked-in C++ suite based on the canonical problem-specifications cases. `.meta/tests.toml` is the generated/synced metadata list for those case descriptions; it is not the C++ source generator. CMake's `build/` directory is generated output and is not a configured exercise file. Keep the learner stubs, generated build files, and maintained test source in their distinct roles.

Run the full path, fixture, and reference checks with:

```sh
python3 work/R20-T018/check.py
```
