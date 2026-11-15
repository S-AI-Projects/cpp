# Maintenance of Acronym Tests

## Test Maintenance Approach

The tests for the `acronym` exercise are hand-maintained in `acronym_test.cpp`. No per-exercise Jinja template exists for this exercise.

## Test Cases and Source

The canonical test cases originate from Exercism's shared problem specifications (`problem-specifications/exercises/acronym/canonical-data.json`) and are tracked in `.meta/tests.toml`:

- `basic` (UUID: `1e22cceb-c5e4-4562-9afe-aef07ad1eaf4`): "Portable Network Graphics" -> "PNG"
- `lowercase_words` (UUID: `79ae3889-a5c0-4b01-baf0-232d31180c08`): "Ruby on Rails" -> "ROR"
- `punctuation` (UUID: `ec7000a7-3931-4a17-890e-33ca2073a548`): "First In, First Out" -> "FIFO"

These three test cases were initially implemented during the exercise introduction (mapped from canonical data) and correspond to the matching entries in `.meta/tests.toml`.

## Reproduction and Verification

To verify the test suite and ensure that all cases pass, build and execute the tests with `EXERCISM_RUN_ALL_TESTS=ON`:

```bash
cmake -S exercises/practice/acronym -B exercises/practice/acronym/build -DEXERCISM_RUN_ALL_TESTS=ON && cmake --build exercises/practice/acronym/build && ./exercises/practice/acronym/build/acronym -s
```

Alternatively, when verifying within an isolated build environment or after copying the exemplar/example solution files (`.meta/example.cpp` and `.meta/example.h` to `acronym.cpp` and `acronym.h`):

```bash
cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON && cmake --build build && ./build/acronym -s
```

## Reproducibility and Idempotency

Generating or copying the tests twice yields identical files (ignoring timestamps) with no cases silently dropped. All cases tracked in `.meta/tests.toml` remain accounted for in `acronym_test.cpp`.
