# R20-T043 Study Notes — `dnd-character` Mutation Analysis

## 1. Inspected Files

- `exercises/practice/dnd-character/.docs/introduction.md` (lines 1–10) & `.docs/instructions.md` (lines 1–32):
  - Six ability scores (`strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, `charisma`) are each rolled as 4d6 keeping the largest 3 (`3..18`).
  - `instructions.md:10`: Constitution modifier is `(constitution - 10) / 2` rounded **down** ($\lfloor (\text{score} - 10) / 2 \rfloor$). Example (`instructions.md:23`): constitution `3` -> modifier `-4`, hitpoints `6`.
- `exercises/practice/dnd-character/.meta/config.json` (lines 1–21):
  - `solution`: `["dnd_character.cpp", "dnd_character.h"]`, `test`: `["dnd_character_test.cpp"]`, `example`: `[".meta/example.cpp", ".meta/example.h"]`. No `editor` key.
- `exercises/practice/dnd-character/dnd_character.cpp` & `.h`: Unsolved learner stubs (`// TODO: add your solution here`).
- `exercises/practice/dnd-character/.meta/example.cpp:9-11`:
  - `int modifier(int score) { return std::floor((static_cast<double>(score) - 10) / 2); }`
- `exercises/practice/dnd-character/.meta/example.h:7-24`:
  - `Character::Character()` calls `ability()` for each attribute and sets `hitpoints = 10 + modifier(constitution);`.
- `exercises/practice/dnd-character/.meta/tests.toml` (lines 1–74):
  - `20` total canonical entries: `18` included (`score 3` through `score 18`, `random ability is within range`, `random character is valid`), `2` excluded (`2ca77b9b-c099-46c3-a02c-0d0f68ffa0fe` and `dca2b2ec-f729-4551-84b9-078876bb4808` — `"each ability is only calculated once"`, `"changes for member variable test not suitable for C++"`).
- `exercises/practice/dnd-character/dnd_character_test.cpp` (lines 1–130):
  - Contains `18` `TEST_CASE` blocks matching the `18` included UUIDs.
  - Anchor cases:
    - `dnd_character_test.cpp:29-32`: `"ability modifier for score 3 is -4"` (`[1e9ae1dc-35bd-43ba-aa08-e4b94c20fa37]`)
    - `dnd_character_test.cpp:36-39`: `"ability modifier for score 4 is -3"` (`[cc9bb24e-56b8-4e9e-989d-a0d1a29ebb9c]`)
    - `dnd_character_test.cpp:41-44`: `"ability modifier for score 5 is -3"` (`[5b519fcd-6946-41ee-91fe-34b4f9808326]`)

## 2. Mutant Analysis

- **Mutant (`work/R20-T043/mutant.cpp`):** Replaces `std::floor((static_cast<double>(score) - 10) / 2)` with `(score - 10) / 2`.
- Because C++ signed integer division truncates toward zero, `(score - 10) / 2` disagrees with `std::floor` on every odd score below `10`:
  - `score = 3`: expected `-4`, mutant `-3` -> FAILS `"ability modifier for score 3 is -4"` (`1e9ae1dc-35bd-43ba-aa08-e4b94c20fa37`)
  - `score = 5`: expected `-3`, mutant `-2` -> FAILS `"ability modifier for score 5 is -3"` (`5b519fcd-6946-41ee-91fe-34b4f9808326`)
  - `score = 7`: expected `-2`, mutant `-1` -> FAILS `"ability modifier for score 7 is -2"` (`099440f5-0d66-4b1a-8a10-8f3a03cc499f`)
  - `score = 9`: expected `-1`, mutant `0` -> FAILS `"ability modifier for score 9 is -1"` (`c70f0507-fa7e-4228-8463-858bfbba1754`)
- **Minimal rejecting input:** `score = 3` (minimum valid ability score in `[3, 18]`), caught directly by `"ability modifier for score 3 is -4"`.
