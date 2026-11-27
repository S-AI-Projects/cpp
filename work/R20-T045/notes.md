# R20-T045 Study Notes — `beer-song` Cost & Operation Study

## 1. Inspected Files

- `exercises/practice/beer-song/.docs/instructions.md` (lines 1–307): Full 100-verse lyrics (`99` bottles down to `0` / "No more bottles"). Supported specification domain is `0..99` bottles (`1` to `100` verses).
- `exercises/practice/beer-song/.meta/config.json` (lines 1–29):
  - `solution`: `["beer_song.cpp", "beer_song.h"]`, `test`: `["beer_song_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/beer-song/beer_song.cpp` & `beer_song.h` (lines 1–7 each): Unsolved learner stubs.
- `exercises/practice/beer-song/.meta/example.h` (lines 1–11): Public functions `verse(unsigned)`, `sing(unsigned, unsigned)`, `sing(unsigned)`.
- `exercises/practice/beer-song/.meta/example.cpp` (lines 1–73):
  - `struct bottles` (`lines 11-15`): stores `unsigned const count` and `string const suffix` (`"s"` if `num > 1`, else `""`).
  - `operator<<` (`lines 17-24`): inserts `b.count`, `" bottle"`, `b.suffix`, and `" of beer"` when `b.count > 0` (`4` leaf insertions), or `"no more bottles"` and `" of beer"` when `b.count == 0` (`2` leaf insertions).
  - `bottles_of_beer_on_the_wall(ostream&, unsigned count)` (`lines 26-33`):
    - If `count > 0`: `stream << bottles(count) << " on the wall, " << bottles(count) << ".\n"` (`2` `bottles` constructions, `4` top-level `<<` ops, `10` leaf `<<` ops).
    - If `count == 0`: `stream << "No more bottles of beer on the wall, " << bottles(count) << ".\n"` (`1` `bottles` construction, `3` top-level `<<` ops, `4` leaf `<<` ops).
  - `take_one_down_and_pass_it_around` (`lines 35-46`): `0` or `1` `bottles` construction, constant number of `<<` insertions.
  - `sing(begin, end)` (`lines 61-69`): calls `verse(stream, num)` for `num = begin` down to `end` (`begin - end + 1` verses) with `begin - end` `'\n'` separators.
- `exercises/practice/beer-song/.meta/tests.toml` (`8` entries, all included) vs `exercises/practice/beer-song/beer_song_test.cpp` (`5` hand-named `TEST_CASE`s without UUID tags):
  - Named cases: `"prints_an_arbitrary_verse"` (`verse(8)`), `"handles_1_bottle"` (`verse(1)`), `"handles_0_bottles"` (`verse(0)`), plus `"sings_several_verses"` (`sing(8, 6)`), `"sings_the_rest_of_the_verses"` (`sing(3)`).
