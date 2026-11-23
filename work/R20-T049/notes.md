# R20-T049 Study Notes — `bank-account` Isolated Runner

## 1. Inspected Files

- `exercises/practice/bank-account/.docs/instructions.md` (lines 1–10): Open/close account, deposit/withdraw funds thread-safely, reject operations on closed accounts.
- `exercises/practice/bank-account/CMakeLists.txt` (lines 1–71):
  - Standard C++17 recipe + `find_package(Threads REQUIRED)` and `target_link_libraries(${exercise} PRIVATE Threads::Threads)` (`lines 44-46`).
- `exercises/practice/bank-account/.meta/config.json` (lines 1–19): `solution`: `["bank_account.cpp", "bank_account.h"]`, `test`: `["bank_account_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/bank-account/bank_account.cpp` & `.h`: Minimal unsolved stubs (`namespace Bankaccount {}` / `class Bankaccount {};`).
- `exercises/practice/bank-account/.meta/example.cpp` (lines 1–57) & `.h` (lines 1–22): Protects `deposit`, `withdraw`, and `balance` with `std::lock_guard guard(mutex_);`.
- `exercises/practice/bank-account/.meta/tests.toml` (`17` entries, all included) & `bank_account_test.cpp` (`17` `TEST_CASE`s, all tagged `[uuid]`):
  - Named cases:
    1. `"Newly opened account has zero balance"` (`983a1528-4ceb-45e5-8257-8ce01aceb5ed`, `lines 11-16`)
    2. `"Single deposit"` (`e88d4ec3-c6bf-4752-8e59-5046c44e3ba7`, `lines 19-24`)
    3. `"Multiple deposits"` (`3d9147d4-63f4-4844-8d2b-1fee2e9a2a0d`, `lines 26-32`)
  - Multithreaded stress case: `"Can handle concurrent transactions"` (`lines 146-167`, `1000` `std::thread`s sleeping `5ms`).
  - Upstream minor typo noted (left untouched): `bank_account_test.cpp:63` has `"annot check balance of closed account"`.
