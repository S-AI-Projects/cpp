# R20-T044 Study Notes — `anagram` Reference Readability Refactor

## 1. Inspected Files

- `exercises/practice/anagram/.docs/instructions.md` (lines 1–12): Specifies finding candidate words that are case-insensitive anagrams of a target word while preserving original candidate casing and excluding the target word itself (case-insensitively).
- `exercises/practice/anagram/.meta/config.json` (lines 1–31):
  - `solution`: `["anagram.cpp", "anagram.h"]`, `test`: `["anagram_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/anagram/anagram.cpp` & `anagram.h` (lines 1–7 each): Unsolved learner stubs.
- `exercises/practice/anagram/.meta/example.h` (lines 1–19): Public class `anagram::anagram` with constructor `anagram(std::string const& subject)`, method `std::vector<std::string> matches(std::vector<std::string> const& matches)`, and private members `subject_` and `key_`. Kept completely unchanged.
- `exercises/practice/anagram/.meta/tests.toml` (lines 1–88): `22` canonical entries (`16` included, `6` excluded).
- `exercises/practice/anagram/anagram_test.cpp` (lines 1–172): `16` `TEST_CASE` blocks (`15` tagged with `[findAnagrams][<uuid>]`, and `"no_matches"` at lines 37–42 untagged corresponding to `dd40c4d2-3c8b-44e5-992a-f42b393ec373`).

## 2. Named Case Trace & Deciding Local State

1. **`no_matches`** (`anagram_test.cpp:37-42`, `subject = "diaper"`, `candidates = {"hello", "world", "zombies", "pants"}` -> `{}`):
   - `subject_ = "diaper"`, `key_ = "adeipr"` (`length == 6`).
   - `"hello"` and `"world"` (`length 5`) fail `candidate.length() != subject_key.length()`.
   - `"zombies"` (`length 7`) fails `candidate.length() != subject_key.length()`.
   - `"pants"` (`length 5`) fails length check. `result` remains `{}`.
2. **`detects_two_anagrams`** (`anagram_test.cpp:45-51`, `subject = "solemn"`, `candidates = {"cherry", "melons", "lemons"}` -> `{"lemons", "melons"}`):
   - `subject_ = "solemn"`, `key_ = "elmnos"` (`length == 6`).
   - `"cherry"` (`length 6`): `to_lower_copy("cherry") != "solemn"`, `make_key("cherry") = "cehrry" != "elmnos"` -> rejected.
   - `"melons"` (`length 6`): `to_lower_copy("melons") != "solemn"`, `make_key("melons") = "elmnos" == key_` -> accepted (`result[0] = "melons"`).
   - `"lemons"` (`length 6`): `to_lower_copy("lemons") != "solemn"`, `make_key("lemons") = "elmnos" == key_` -> accepted (`result[1] = "lemons"`).
3. **`does_not_detect_anagram_subsets`** (`anagram_test.cpp:53-59`, `subject = "good"`, `candidates = {"dog", "goody"}` -> `{}`):
   - `subject_ = "good"`, `key_ = "dgoo"` (`length == 4`).
   - `"dog"` (`length 3`) and `"goody"` (`length 5`) both fail `candidate.length() != subject_key.length()`. `result` remains `{}`.

## 3. Scoped Readability Refactor

- Renamed `anagram::matches` parameter `matches` -> `candidates` (resolves shadowing of method name `anagram::matches`) and loop element `s` -> `candidate`.
- Hoisted `const string lowered_subject = to_lower_copy(subject_);` outside the loop rather than re-lowercasing `subject_` for every candidate.
- Extracted `is_anagram_candidate(candidate, lowered_subject, subject_key)` with early-return checks (length mismatch, case-insensitive self-match, sorted-key equality) and added an explicit invariant comment above `anagram::matches`.
- Left `.meta/example.h` unchanged and intentionally avoided fixing unrelated pre-existing details (`std::tolower(c)` without `unsigned char` cast, `using namespace std;`), noting them for completeness.
