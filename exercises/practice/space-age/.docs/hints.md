# Hints

## General

- Consider storing the age in seconds provided to the constructor.
- One Earth year equals 31,557,600 seconds.
- Orbital periods for other planets are expressed relative to Earth years.

## Decision Table

The table below summarizes the test inputs and required outcomes based on the test suite:

| Test Case | Input (`seconds`) | Method Called | Expected Output | Tolerance / Notes |
| :--- | :--- | :--- | :--- | :--- |
| `age_in_seconds` | `1000000` | `seconds()` | `1000000` | Exact integer match |
| `age_in_earth_years` | `1000000000` | `on_earth()` | `31.69` | Within `0.005` |
| `age_in_mercury_years` | `2134835688` | `on_earth()` | `67.65` | Within `0.005` |
| `age_in_mercury_years` | `2134835688` | `on_mercury()` | `280.88` | Within `0.005` |

### Unspecified Behavior

The exercise specification does not specify behavior for non-standard inputs such as negative ages, values outside normal integer/floating-point bounds, or queries for invalid planets (note that the problem specification's `"invalid planet causes error"` case is excluded from this C++ track's test suite as methods are statically defined for each valid planet). Implementations should not introduce extra exception handling, input validation, or coercion rules beyond what is required by the source specification and test suite.
