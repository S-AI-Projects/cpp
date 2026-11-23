# R20-T042 Study Notes — `pig-latin` Test-Generation & Preparation Path

## 1. Inspected Files

- `exercises/practice/pig-latin/.docs/instructions.md` (lines 1–46): Defines Pig Latin translation across four rules:
  - Rule 1 (lines 10–18): Words beginning with a vowel (`a`, `e`, `i`, `o`, `u`) or `"xr"` / `"yt"` get `"ay"` appended (`"apple"` -> `"appleay"`, `"xray"` -> `"xrayay"`, `"yttria"` -> `"yttriaay"`).
  - Rule 2 (lines 20–28): Leading consonant cluster moves to the end followed by `"ay"`.
  - Rule 3 (lines 30–37): Zero or more consonants followed by `"qu"` move together to the end followed by `"ay"`.
  - Rule 4 (lines 39–46): One or more consonants followed by `"y"` move the consonants preceding `"y"` to the end followed by `"ay"`.
- `exercises/practice/pig-latin/.meta/config.json` (lines 1–21):
  - `files.solution`: `["pig_latin.cpp", "pig_latin.h"]`
  - `files.test`: `["pig_latin_test.cpp"]`
  - `files.example`: `[".meta/example.cpp", ".meta/example.h"]`
  - No `editor` key is present.
- `exercises/practice/pig-latin/pig_latin.h` & `pig_latin.cpp` (lines 1–7 each): Unsolved learner stubs (`// TODO: add your solution here`).
- `exercises/practice/pig-latin/.meta/example.h` (lines 1–9) & `example.cpp` (lines 1–30):
  - Declares `std::string translate(const std::string& phrase);`.
  - `translate_word` (`example.cpp:4-14`) checks vowel/`"yt"`/`"xr"` prefixes first, then `"thr"`, `"sch"`, `"squ"`, `"ch"`, `"qu"`, `"th"`, `"rh"`, else rotates 1 consonant + `"ay"`.
  - `translate` (`example.cpp:16-29`) splits space-delimited words and joins translated words.
- `exercises/practice/pig-latin/.meta/tests.toml` (lines 1–79):
  - Generated/synced by `configlet sync` (`.github/workflows/run-configlet-sync.yml` / `bin/configlet`).
  - Contains `23` canonical UUID entries, all included (omitted `include` key implies `include = true`, `0` excluded).
- `exercises/practice/pig-latin/pig_latin_test.cpp` (lines 1–111):
  - Hand-maintained Catch2 test file (no per-exercise test generator or Jinja template exists; `exercises/practice/knapsack/.meta/create_tests.py` is the only per-exercise generator in this repository).
  - Contains `23` `TEST_CASE` blocks; every block carries its exact `tests.toml` UUID as a Catch2 tag (`[uuid]`).
  - First case (`"word beginning with a"`, lines 8–10) sits outside `#if defined(EXERCISM_RUN_ALL_TESTS)` (`line 12`); cases 2–23 (`lines 14-109`) sit inside `#if defined(EXERCISM_RUN_ALL_TESTS)` ... `#endif` (`line 111`).
- Track generator / CI entry points:
  - Root `CMakeLists.txt` (lines 4–42): `option(EXERCISM_RUN_ALL_TESTS ... On)`, `option(EXERCISM_COMMON_CATCH ... On)`, and `build_fixup()` (`lines 4-17`), which copies `exercises/practice/<slug>` into `build_exercises/practice/<slug>` and renames `.meta/example.h` -> `<file>.h` and `.meta/example.cpp` -> `<file>.cpp`.
  - `.github/workflows/ci.yml` (lines 12–90): Configures at root (`cmake -G Ninja .` / `cmake .`) and removes Boost-dependent `gigasecond` and `meetup` when Boost is absent (`lines 72-73`).
  - `.github/workflows/run-configlet-sync.yml` & `.github/workflows/configlet.yml`: Run `exercism/github-actions` `configlet-sync` / `configlet` on `tests.toml`.

## 2. Configlet Sync Observation (`configlet 4.0.3`)

Running `./bin/fetch-configlet` and `./bin/configlet sync --tests --exercise pig-latin` (without `--update`) in an isolated temp copy of `org/main`:
- `configlet 4.0.3` cloned `exercism/problem-specifications` and exited `1` with:
  - `[warn] pig-latin: missing 2 test cases` (`44616581-5ce3-4a81-82d0-40c7ab13d2d0` and `44616581-5ce3-4a81-82d0-40c7ab13d2d1`, both `"phrases are translated -> a whole phrase"` added upstream after pinned commit `8d139cb04c7463722ae1f233099cc0bd39a71092`).
- At the pinned repo state (`8d139cb04c7463722ae1f233099cc0bd39a71092`), `tests.toml` (`23` included entries) and `pig_latin_test.cpp` (`23` UUID-tagged `TEST_CASE`s) match 1-to-1 with zero missing or extra UUIDs.

## 3. Three Anchor Cases Trace

| UUID | Test Name | Lines in `pig_latin_test.cpp` | Input | Expected Output |
| :--- | :--- | :---: | :--- | :--- |
| `11567f84-e8c6-4918-aedb-435f0b73db57` | `"word beginning with a"` | `8-10` | `"apple"` | `"appleay"` |
| `f623f581-bc59-4f45-9032-90c3ca9d2d90` | `"word beginning with e"` | `14-16` | `"ear"` | `"earay"` |
| `7dcb08b3-23a6-4e8a-b9aa-d4e859450d58` | `"word beginning with i"` | `18-20` | `"igloo"` | `"iglooay"` |

## 4. Timestamp Normalization

Neither `exercises/practice/pig-latin/pig_latin_test.cpp` nor `CMakeLists.txt:build_fixup()` embeds timestamps or host-specific metadata into prepared test files. Therefore, the normalization step before comparing two independent preparations is the identity function (`normalise(text) == text`), and raw SHA-256 hashes of `build_exercises/practice/<slug>/<file>_test.cpp` and the substituted solution files match byte-for-byte across independent runs.
