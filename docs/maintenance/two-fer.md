# two-fer canonical case notes

This note reviews the three canonical cases defined for `two-fer` and compares them with the maintained C++ reference in `.meta/example.h`. It documents current test coverage and design decisions without modifying canonical case inclusions or learner starter files.

| Canonical UUID | Canonical input | Expected | C++ test / rationale |
| --- | --- | --- | --- |
| `1cf3e15a-a3d7-4a87-aeb3-ba1b43bc8dce` | `name=null / none` | `"One for you, one for me."` | Covered by `no_name_given`. In C++, default argument syntax (`const std::string& name = "you"`) allows parameterless calls (`two_fer::two_fer()`), returning `"One for you, one for me."`. |
| `b4c6dbb8-b4fb-42c2-bafd-10785abe7709` | `name="Alice"` | `"One for Alice, one for me."` | Covered by `a_name_given`. The string argument binds to `const std::string& name`, and string concatenation yields `"One for Alice, one for me."`. |
| `3549048d-1a6e-4653-9a79-b0bda163e8d5` | `name="Bob"` | `"One for Bob, one for me."` | Covered by `another_name_given`. Validates arbitrary name substitution with `"Bob"`, returning `"One for Bob, one for me."`. |

The reference implementation defines:
```cpp
namespace two_fer {
inline std::string two_fer(const std::string& name = "you") {
    return "One for " + name + ", one for me.";
}
}
```
All three canonical cases are directly enabled and supported by this reference without language limitations or exclusions.

## Coverage snapshot

Before and after this documentation addition:
- `.meta/tests.toml` contains 3 canonical UUID entries and 0 explicit `include = false` exclusions.
- C++ test suite (`two_fer_test.cpp`) contains 3 test cases, all enabled under `EXERCISM_RUN_ALL_TESTS`.
- Learner starter files (`two_fer.h`, `two_fer.cpp`) remain unsolved.

The focused check can be executed from the repository root:
```sh
python3 work/R20-T021/check.py
```

The checker copies the exercise (including dotfiles) into a temporary directory, substitutes the reference solution in that isolated copy, builds via CMake, and runs the test suite and a canonical input probe.
