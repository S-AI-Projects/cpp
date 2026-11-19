# Hello World Maintenance Documentation

## Overview

This document records the mutation analysis, target test cases, and expected validation behavior for `exercises/practice/hello-world`.

## Canonical Test Case

- **Canonical Description**: "Say Hi!"
- **Canonical UUID**: `af9ffe10-dc13-42d8-a742-e7bdafac449d` (referenced as `af9a35e4-1844-4731-8646-95f6b645b23e` in specification alias)
- **Catch2 Test Case**: `test_hello`
- **Assertion**:
  ```cpp
  REQUIRE(hello_world::hello() == "Hello, World!");
  ```
- **Expected Return**: `"Hello, World!"` (exact string with capitalization, comma delimiter, space, and exclamation point).

## Formulated Mutant

To verify that the test suite catches subtle formatting bugs rather than just loose substring matches, we formulate the following mutant:

```diff
--- exercises/practice/hello-world/.meta/example.cpp
+++ mutant.cpp
@@ -5,3 +5,3 @@
 namespace hello_world {

-string hello() { return "Hello, World!"; }
+string hello() { return "Hello World!"; } // mutant: missing comma

 }  // namespace hello_world
```

### Evaluation of Mutant

1. **Compilation**: The mutant returns `std::string` and compiles without errors against `hello_world.h`.
2. **Partial / Tautological Checks**: The mutant would pass weak assertions such as:
   - `!hello().empty()` (non-empty string check)
   - `hello().rfind("Hello", 0) == 0` (prefix check)
   - `hello().back() == '!'` (terminator check)
3. **Rejecting Test**: The canonical test `test_hello` (`Say Hi!`) rejects this mutant with:
   ```
   CHECK( hello_world::hello() == "Hello, World!" )
   with expansion:
     "Hello World!" == "Hello, World!"
   ```
4. **Conclusion**: The Catch2 assertion strictly enforces the contract against the punctuation mutant.
