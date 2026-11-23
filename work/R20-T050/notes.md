# R20-T050 Study Notes — `darts` Contract & Decision Table

## 1. Inspected Files

- `exercises/practice/darts/.docs/instructions.md` (lines 1–31): Concentric circles at `(0, 0)` with radii `1` (`10` pts), `5` (`5` pts), `10` (`1` pt), outside (`0` pts), for Cartesian real `(x, y)`.
- `exercises/practice/darts/.meta/config.json` (lines 1–23): `solution`: `["darts.cpp", "darts.h"]`, `test`: `["darts_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/darts/darts.cpp` & `.h` (lines 1–7 each): Unsolved learner stubs.
- `exercises/practice/darts/.meta/example.cpp` (lines 1–21) & `.meta/example.h` (lines 1–7):
  - `int score(float x, float y)` computes `auto distance = std::hypot(x, y);` and checks `distance <= 1.0` -> `10`, `<= 5.0` -> `5`, `<= 10.0` -> `1`, else `0`.
- `exercises/practice/darts/.meta/tests.toml` (`13` entries, all included) and `darts_test.cpp` (`13` hand-named `TEST_CASE`s without UUID tags):
  - Named cases:
    1. `darts_test.cpp:8`: `TEST_CASE("missed_target") { REQUIRE(darts::score(-9, 9) == 0); }`
    2. `darts_test.cpp:11`: `TEST_CASE("on_the_outer_circle") { REQUIRE(darts::score(0, 10) == 1); }`
    3. `darts_test.cpp:13`: `TEST_CASE("on_the_middle_circle") { REQUIRE(darts::score(-5, 0) == 5); }`
