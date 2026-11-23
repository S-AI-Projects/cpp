# Bank Account (`exercises/practice/bank-account`) — Isolated Test Runner

## Overview

`tools/course_checks/r20-t049.py` builds and runs `exercises/practice/bank-account` (and any other Exercism C++ practice exercise via `--exercise <slug>`) inside an isolated temporary directory (`r20-t049-*`) so learner stubs and test files are never altered and `build/` artifacts never pollute the repository working tree.

## Command & Options

Run from the repository root:

```bash
python3 tools/course_checks/r20-t049.py --exercise bank-account
```

Supported flags:
- `--exercise <slug>` — Exercise directory under `exercises/practice/` (default: `bank-account`).
- `--reference-dir <dir>` — Optional directory supplying alternative reference files (`example.cpp`/`.h` or `<file>.cpp`/`.h`) instead of `.meta/example.*`.
- `--filter <catch-test-spec>` — Optional Catch2 test filter expression.
- `--xml-out <path>` / `--list-out <path>` — Optional paths to save Catch2 XML and `--list-test-names-only` output outside the temp tree.

Full coursework scenario verification:

```bash
python3 work/R20-T049/check.py
```

Expected final output:

```text
RESULT: PASS - executed 17 cases
```

## Tool Requirements

- **C++17 compiler** (`-Wall -Wextra -Wpedantic -Werror` in `exercises/practice/bank-account/CMakeLists.txt:48-54`)
- **CMake** (`>= 3.5.1` declared; tested with `4.5.1`)
- **POSIX Threads (`Threads::Threads`)**: required by `exercises/practice/bank-account/CMakeLists.txt:44-46` (`find_package(Threads REQUIRED)` / `target_link_libraries(${exercise} PRIVATE Threads::Threads)`) for `std::thread` concurrency case `"Can handle concurrent transactions"` (`bank_account_test.cpp:146-167`, `1000` threads)
- **Python 3.9+** (standard library only)

## Verified Scenarios & Exit Codes

| Scenario | Command / Condition | Expected Exit Code | Observed Behavior |
| :--- | :--- | :---: | :--- |
| Real reference | `python3 tools/course_checks/r20-t049.py --exercise bank-account` | `0` | Configures, links `Threads::Threads`, executes all `17/17` Catch2 cases (`RESULT: PASS - executed 17 cases`). |
| Deliberately failing reference | `--reference-dir <tmp>/bad_ref` (`balance_ += amount + 1;`) | `1` (non-zero) | Compiles cleanly under `-Werror`, fails assertions in Catch2 XML, propagates failure as exit code `1`. |
| Empty test selection | `--filter "no-such-test*"` | `1` (non-zero) | Catch2 exits `0` with `0` executed tests; `ZERO-TEST GUARD` (`OverallResultsCases successes+failures == 0`) fails and exits `1`. |
| Interrupted run (`SIGINT`) | Send `SIGINT` after `TEMP_DIR:` is printed mid-build | Non-zero (`1` / `-2`) | Signal handler terminates child `cmake`/compiler process, removes `r20-t049-*` temp dir in `finally:`, and preserves SHA-256 hashes. |

## Safety Guarantees

1. **Learner File Hash Invariant:** All files under `exercises/practice/bank-account` are SHA-256 hashed before starting and re-hashed in `finally:` across every scenario (success, failure, empty filter, and `SIGINT`/`SIGTERM`).
2. **Guaranteed Temp Cleanup:** `r20-t049.py` prints `TEMP_DIR: <path>` immediately upon creation and removes `<path>` inside `finally:` (backed by `SIGINT` and `SIGTERM` signal handlers).
3. **Zero-Test Guard:** Prevents Catch2's default `exit 0` on `"No tests ran"` from producing a false pass.
