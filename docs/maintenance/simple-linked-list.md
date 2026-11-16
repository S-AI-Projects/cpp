# Simple-linked-list reference runner

Run the maintained reference suite from the repository root:

```sh
python3 tools/course_checks/r20-t019.py
```

The runner reads the `solution`, `test`, and `example` paths from `exercises/practice/simple-linked-list/.meta/config.json`. It copies the exercise, including dotfiles, to a temporary directory, copies the configured example implementation and header to the solution paths there, then runs the CMake configure/build commands and reads the executable's JUnit report. It reports the number and names of executed test cases, child statuses, and SHA-256 hashes of the learner files before and after the run.

The temporary copy is removed after success, assertion failure, zero selected tests, timeout, or interruption. A normal successful run exits `0`; test/build failures exit `1`; an empty selection exits `2`; a timed-out child exits `124`; and an interrupted run exits `130`. A zero-case JUnit report is always treated as failure.

Useful validation options:

```sh
python3 tools/course_checks/r20-t019.py --selection none
python3 tools/course_checks/r20-t019.py --timeout-seconds 30
```

`--reference-source PATH` substitutes an alternate reference source only inside the temporary copy, for checking failure propagation. `--temp-parent DIR` places the disposable copy under a caller-selected directory so cleanup can be verified. Requirements are Python 3.10 or later, CMake, and a C++17 compiler.

This exercise does not contain `.meta/tests.toml`; the runner reports the actual cases executed by Catch2 instead of inferring the case count from absent metadata. The checked-in `simple_linked_list_test.cpp` names the canonical cases, and CMake builds that file with the configured solution source.
