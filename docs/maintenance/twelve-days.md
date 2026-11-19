# twelve-days mutation-driven regression notes

This document records a deliberate mutant in `exercises/practice/twelve-days/`, identifies the existing Catch2 test case that rejects it, and specifies the minimal distinguishing input under the specification contract.

## The Deliberate Mutant

In `exercises/practice/twelve-days/.meta/example.cpp`, the inner loop of `verse(int day)` constructs gifts for earlier days:

```cpp
for (int i = day - 1; i >= 1; --i) {
    if (i == 1) {
        result += std::string{", and "};
    } else {
        result += std::string{", "};
    }
    result += gifts[i];
}
```

The mutant simulates a common learner error where all gifts in a multi-gift verse are concatenated with a uniform comma separator `", "`, neglecting the conjunction `", and "` preceding the final gift:

```diff
-        if (i == 1) {
-            result += std::string{", and "};
-        } else {
+        {
             result += std::string{", "};
         }
```

## Rejecting Test Case

- **Test Name**: `second day two turtle doves`
- **Canonical UUID**: `1c64508a-df3d-420a-b8e1-fe408847854a`
- **Minimal Distinguishing Input**: `twelve_days::recite(2, 2)`
  - Verse 1 has only one gift (`"a Partridge in a Pear Tree"`), which does not use a conjunction.
  - Verse 2 is the smallest input allowed by the specification where multiple gifts exist and the conjunction `", and "` is required.
- **Expected Output**:
  ```
  On the second day of Christmas my true love gave to me: two Turtle Doves, and a Partridge in a Pear Tree.\n
  ```
- **Mutant Output**:
  ```
  On the second day of Christmas my true love gave to me: two Turtle Doves, a Partridge in a Pear Tree.\n
  ```

Because Catch2 test `second day two turtle doves` directly checks `expected == twelve_days::recite(2, 2)`, it immediately rejects the mutant. The existing suite already catches this regression, so no additional canonical test cases are required.

## Automated Verification

The automated regression check is implemented in `work/R20-T023/check.py`:
- Validates the unmodified reference solution in an isolated temporary build; all 15 test cases pass (exit code 0).
- Applies the deliberate mutant in a separate isolated temporary build and verifies that `second day two turtle doves` fails (1 test case failed, 1 assertion failed, non-zero exit code).
- Confirms learner starter files remain unchanged and unsolved.

Run the check from repository root:
```sh
python3 work/R20-T023/check.py
```
