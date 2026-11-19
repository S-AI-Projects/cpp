# Leap Test Generation and Maintenance Documentation

## Overview

This document describes the test generation and maintenance workflow for `exercises/practice/leap` in the Exercism C++ track. It maps canonical test specifications from `exercises/practice/leap/.meta/tests.toml` to the C++ test suite `exercises/practice/leap/leap_test.cpp`.

## Input Files and File Roles

As defined in `exercises/practice/leap/.meta/config.json`:
- **Solution files (learner-facing stubs)**:
  - `exercises/practice/leap/leap.cpp`: Empty/stub implementation file.
  - `exercises/practice/leap/leap.h`: Function declarations for the learner.
- **Test files**:
  - `exercises/practice/leap/leap_test.cpp`: Catch2 test suite.
  - `exercises/practice/leap/test/tests-main.cpp`: Catch2 test entry point.
- **Reference files**:
  - `exercises/practice/leap/.meta/example.h`: Canonical reference solution used for CI and track verification.
- **Metadata files**:
  - `exercises/practice/leap/.meta/config.json`: File manifests and exercise metadata.
  - `exercises/practice/leap/.meta/tests.toml`: Canonical UUIDs and case descriptions synced from problem-specifications.

## Generation Route and Tooling

1. **Configlet Sync**:
   Canonical test cases are synchronized from the central `problem-specifications` repository using `configlet`:
   ```bash
   ./bin/fetch-configlet
   ./bin/configlet sync --exercise leap
   ```
2. **Template vs Hand-Maintained Tests**:
   Unlike tracks that employ per-exercise Jinja templates, the C++ track maintains Catch2 test files (`leap_test.cpp`) directly aligned with the canonical UUID cases in `tests.toml`. The Catch2 macros (`TEST_CASE`, `REQUIRE`) structure the test cases.
3. **Execution Command**:
   ```bash
   cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON
   cmake --build build
   ./build/leap
   ```

## Case-to-Output Mapping

| Canonical UUID | Canonical Description | Catch2 Test Case Name | Assertion | Expected Result |
|---|---|---|---|---|
| `6466b30d-519c-438e-935d-388224ab5223` | year not divisible by 4 in common year | `not_divisible_by_4` | `REQUIRE(!leap::is_leap_year(2015));` | `false` |
| `ac227e82-ee82-4a09-9eb6-4f84331ffdb0` | year divisible by 2, not divisible by 4 in common year | `divisible_by_2_not_divisible_by_4` | `REQUIRE(!leap::is_leap_year(1970));` | `false` |
| `4fe9b84c-8e65-489e-970b-856d60b8b78e` | year divisible by 4, not divisible by 100 in leap year | `divisible_by_4_not_divisible_by_100` | `REQUIRE(leap::is_leap_year(1996));` | `true` |
| `78a7848f-9667-4192-ae53-87b30c9a02dd` | year divisible by 100, not divisible by 400 in common year | `divisible_by_100_not_divisible_by_400` | `REQUIRE(!leap::is_leap_year(2100));` | `false` |
| `42ee56ad-d3e6-48f1-8e3f-c84078d916fc` | year divisible by 400 in leap year | `divisible_by_400` | `REQUIRE(leap::is_leap_year(2000));` | `true` |
| `c30331f6-f9f6-4881-ad38-8ca8c12520c1` | year divisible by 200, not divisible by 400 in common year | `divisible_by_200_not_divisible_by_400` | `REQUIRE(!leap::is_leap_year(1800));` | `false` |

## Track-Specific Divergence Notes

- Redundant canonical cases (`7fc6aed7-e63c-48f5-ae05-5fe182f60a5d`, `9d70f938-537c-40a6-ba19-f50739ce8bac`, `57902c77-6fe9-40de-8302-587b5c27121e`) are covered by the core boundary cases (divisible by 4, 100, 400) to keep the compiled test binary compact while maintaining 100% boundary coverage.
- The test suite uses `#if defined(EXERCISM_RUN_ALL_TESTS)` so that beginners see only the first test case by default until configuring `EXERCISM_RUN_ALL_TESTS=ON`.
