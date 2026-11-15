# grade-school test maintenance

The track has two related but separate files for this exercise:

| Role | Path | How it is maintained |
| --- | --- | --- |
| Canonical case descriptions and inclusion | `exercises/practice/grade-school/.meta/tests.toml` | Synced from Exercism problem specifications by `configlet sync`. An omitted `include` key means included; `include = false` disables an entry. |
| C++ test cases and expected values | `exercises/practice/grade-school/grade_school_test.cpp` | Maintained C++ source. There is no grade-school Jinja template or per-exercise test generator in this track. Each active test carries its canonical UUID as a Catch tag. |
| Reference implementation | `exercises/practice/grade-school/.meta/example.cpp` and `.meta/example.h` | Copied into the learner filenames only in the temporary test copy. |

From the repository root, configlet checks or updates the canonical metadata:

```sh
./bin/configlet sync --exercise grade-school --tests
```

To apply a non-interactive metadata update while leaving newly discovered
canonical cases excluded pending C++ tests, run:

```sh
./bin/configlet sync --exercise grade-school --tests exclude --update --yes
```

This command updates
`.meta/tests.toml`; it does not generate `grade_school_test.cpp`. The C++ test
source is the maintained mapping from enabled UUIDs to assertions, and the
exercise CMake file compiles and runs that source.

## Case-to-test mapping

| Canonical UUID | Enabled C++ test | Expected result |
| --- | --- | --- |
| `a3f0fb58-f240-4723-8ddc-e644666b85cc` | `roster_is_empty_when_no_student_is_added` | An empty school has an empty roster. |
| `6d0a30e4-1b4e-472e-8e20-c41702125667` | `student_is_added_to_the_roster` | Adding Aimee to grade 2 yields `{2: ["Aimee"]}`. |
| `233be705-dd58-4968-889d-fb3c7954c9cc` | `multiple_students_in_the_same_grade_are_added_to_the_roster` | Adding Blair, James, and Paul to grade 2 yields the alphabetized roster `{2: ["Blair", "James", "Paul"]}`. |

The test IDs in the C++ source must equal the set of enabled UUIDs in
`tests.toml`; disabled entries must not appear in that source. At this base
revision there are 23 metadata entries: 15 included and 8 explicitly excluded,
matching the 15 UUID-tagged C++ test cases.

The focused checker performs two fresh `configlet sync --tests exclude --update --yes`
runs in isolated track copies and verifies the metadata remains in sync with
problem specifications. Since configlet does not generate the maintained C++
test source, the checker compares the resulting metadata and test source, then
performs two clean CMake generations and compares the compiled test-name lists.
Configlet does not emit a timestamp in these files,
so the comparison is byte-for-byte; no timestamp normalization is needed. Each
build runs the maintained reference suite, and the report records the exact
case count and command outcomes.

Run the task check from the repository root:

```sh
python3 work/R20-T012/check.py
```

The check requires Python 3, CMake, a C++17 compiler, and the track's configlet
binary. Install configlet with `./bin/fetch-configlet` if it is not already
present. All temporary copies include dotfiles; only those copies receive the
reference files as learner solutions.
