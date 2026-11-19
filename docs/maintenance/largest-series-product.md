# Largest Series Product Maintenance Documentation

## Overview

This document records the canonical case mapping, inclusion/exclusion status, and technical rationale for canonical test cases defined in `exercises/practice/largest-series-product/.meta/tests.toml`.

Total canonical cases: 18  
- Included: 13  
- Excluded: 5  

## Case Mapping and Rationale Table

| UUID | Description | Status | Rationale |
|---|---|---|---|
| `7c82f8b7-e347-48ee-8a22-f672323324d4` | finds the largest product if span equals length | Included | Core functional case where `span == digits.length()`. |
| `88523f65-21ba-4458-a76a-b4aaf6e4cb5e` | can find the largest product of 2 with numbers in order | Included | Standard positive test case with increasing sequence. |
| `f1376b48-1157-419d-92c2-1d7e36a70b8a` | can find the largest product of 2 | Included | Standard test case for span 2. |
| `46356a67-7e02-489e-8fea-321c2fa7b4a4` | can find the largest product of 3 with numbers in order | Included | Standard positive test case for span 3. |
| `a2dcb54b-2b8f-4993-92dd-5ce56dece64a` | can find the largest product of 3 | Included | Standard test case for span 3. |
| `673210a3-33cd-4708-940b-c482d7a88f9d` | can find the largest product of 5 with numbers in order | Included | Standard test case for larger span. |
| `02acd5a6-3bbf-46df-8282-8b313a80a7c9` | can get the largest product of a big number | Included | Large input string handling. |
| `76dcc407-21e9-424c-a98e-609f269622b5` | reports zero if the only digits are zero | Included | Zero multiplication semantics. |
| `6ef0df9f-52d4-4a5d-b210-f6fae5f20e19` | reports zero if all spans include zero | Included | Verifies zero-factor evaluation. |
| `5d81aaf7-4f67-4125-bf33-11493cc7eab7` | rejects span longer than string length | Excluded | Superseded by `0ae1ce53-d9ba-41bb-827f-2fceb64f058b` which asserts `std::domain_error`. |
| `0ae1ce53-d9ba-41bb-827f-2fceb64f058b` | rejects span longer than string length | Included | Reimplementation of `5d81aaf7-4f67-4125-bf33-11493cc7eab7` asserting `std::domain_error`. |
| `06bc8b90-0c51-4c54-ac22-3ec3893a079e` | reports 1 for empty string and empty product (0 span) | Excluded | The C++ track test suite omits 0-span empty-product tests to focus on meaningful subseries spans (span >= 1). |
| `3ec0d92e-f2e2-4090-a380-70afee02f4c0` | reports 1 for nonempty string and empty product (0 span) | Excluded | The C++ track test suite omits 0-span empty-product tests to focus on meaningful subseries spans (span >= 1). |
| `6d96c691-4374-4404-80ee-2ea8f3613dd4` | rejects empty string and nonzero span | Excluded | Superseded by `6cf66098-a6af-4223-aab1-26aeeefc7402`. |
| `6cf66098-a6af-4223-aab1-26aeeefc7402` | rejects empty string and nonzero span | Included | Active canonical test asserting `std::domain_error`. |
| `7a38f2d6-3c35-45f6-8d6f-12e6e32d4d74` | rejects invalid character in digits | Included | Error handling asserting `std::domain_error`. |
| `5fe3c0e5-a945-49f2-b584-f0814b4dd1ef` | rejects negative span | Excluded | Superseded by `c859f34a-9bfe-4897-9c2f-6d7f8598e7f0`. |
| `c859f34a-9bfe-4897-9c2f-6d7f8598e7f0` | rejects negative span | Included | Active canonical test asserting `std::domain_error`. |

## Focus Canonical UUIDs Rationale

1. **`5d81aaf7-4f67-4125-bf33-11493cc7eab7` (rejects span longer than string length)**:
   - **Status**: Excluded (`include = false`).
   - **Rationale**: This is a legacy canonical case that has been formally superseded and reimplemented by `0ae1ce53-d9ba-41bb-827f-2fceb64f058b`. In C++, the active reimplementing test verifies that passing a span exceeding the string length throws `std::domain_error`. The original entry is marked `include = false` to prevent duplicate test generation.

2. **`06bc8b90-0c51-4c54-ac22-3ec3893a079e` (reports 1 for empty string and empty product (0 span))**:
   - **Status**: Excluded (`include = false`).
   - **Rationale**: An empty product of span 0 on an empty string represents a degenerate mathematical edge case. The C++ track exercises focus on contiguous slices of positive length (`span >= 1`). While `example.cpp` provides an early return for `span == 0`, the test case is excluded from generation in `tests.toml`.

3. **`3ec0d92e-f2e2-4090-a380-70afee02f4c0` (reports 1 for nonempty string and empty product (0 span))**:
   - **Status**: Excluded (`include = false`).
   - **Rationale**: Similar to `06bc8b90-0c51-4c54-ac22-3ec3893a079e`, 0-span products on non-empty strings are excluded from the test suite in the C++ track to keep the focus on finding products of actual digit series.
