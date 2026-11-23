# Beer Song (`exercises/practice/beer-song`) — Cost & Scaling Study

## Supported Domain & Input Size Definition

- **Supported domain (`exercises/practice/beer-song/.docs/instructions.md:1-307`):** `0..99` bottles (`unsigned count` in `0..99`).
- **Input size (`N`):** Number of verses produced (`1 <= N <= 100`):
  1. `1` verse: `beer_song::verse(8)`
  2. `10` verses: `beer_song::sing(9, 0)`
  3. `100` verses: `beer_song::sing(99, 0)` (full song)

## Complexity & Invariant Summary (`bottles_of_beer_on_the_wall`)

In `exercises/practice/beer-song/.meta/example.cpp:26-39`:

- `bottles_of_beer_on_the_wall(ostream& stream, unsigned count)` performs **$O(1)$ work and $O(1)$ auxiliary stack space per call** within the `0..99` bottle domain (numeric formatting has at most 2 decimal digits, and `bottles::suffix` holds at most `"s"`):
  - For `count > 0`, it constructs **`2`** `bottles` objects and performs **`4`** top-level stream insertions (`10` leaf `<<` insertions through `operator<<`).
  - For `count == 0`, it constructs **`1`** `bottles` object and performs **`3`** top-level stream insertions (`4` leaf `<<` insertions through `operator<<`).
- `sing(begin, end)` (`example.cpp:67-75`) calls `verse(stream, num)` once per verse plus `N - 1` newline separators, so total work scales linearly as $\Theta(N)$ in the number of verses `N = begin - end + 1`.

## Instrumented Operation Counts

Measured by compiling and running an instrumented copy (`work/R20-T045/instrumentation.log`) after asserting exact output equality on all overlapping test expectations (`verse(8)`, `verse(1)`, `verse(0)`, `sing(8, 6)`):

| Call | Verses | `bottles_of_beer_on_the_wall` Calls | `bottles` in `wall` | Top-level `<<` in `wall` | Leaf `<<` in `wall` | Total `bottles` | Total Leaf `<<` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `verse(8)` | `1` | `1` | `2` | `4` | `10` | `3` | `16` |
| `sing(9,0)` | `10` | `10` | `19` | `39` | `94` | `28` | `156` |
| `sing(99,0)` | `100` | `100` | `199` | `399` | `994` | `298` | `1686` |

## Algorithm Timings vs. Compile & Process-Startup Overhead

Measured on macOS `27.2.1` (`arm64`) with `Apple clang version 21.0.0 (clang-2100.4.1.1)`, flags `-std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror`. Specification correctness was asserted before any timing began; all three input sizes were benchmarked inside a single warm process (`50` warm-up passes, `9` timed repetitions of batched calls per size, median reported):

### Compile & Process-Startup Overhead (Measured Separately)

| Phase | Measurement | Value | Notes |
| :--- | :--- | :---: | :--- |
| Minimal empty `main()` compile | `c++ -std=c++17 -O2 noop.cpp -o noop` | `84.84 ms` | Compiler/linker baseline |
| Benchmark + `example.cpp` compile | `c++ -std=c++17 -O2 bench_main.cpp beer_song.cpp` | `933.97 ms` | One-time build cost |
| Process startup / teardown | Median across `9` runs of `./noop` | `4.39 ms` (`4,390 us`) | Dominates single-run wall time (~`127x` larger than full 100-verse `sing(99, 0)`) |

### In-Process Algorithm Timings (`9` Repetitions per Size)

| Call | Verses (`N`) | Batch / Rep | Median (`us`) | Min (`us`) | Max (`us`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `verse(8)` | `1` | `500` | `0.661` | `0.628` | `0.751` |
| `sing(9,0)` | `10` | `200` | `3.712` | `3.271` | `3.726` |
| `sing(99,0)` | `100` | `50` | `34.580` | `30.032` | `41.209` |

## Limits of Conclusion

- The exercise specification bounds valid input to `0..99` bottles (`1..100` verses), making this a small, fixed-domain workload where process startup (`~4.39 ms`) and compilation (`~934 ms`) dwarf in-memory formatting (`~34.6 us` for all 100 verses).
- Passing large inputs outside `0..99` is outside the specification; asymptotically, `sing(N, 0)` would remain $\Theta(N \log N_{\max})$ due to decimal digit formatting and `ostringstream` buffer growth, while `bottles_of_beer_on_the_wall` stays $O(1)$ per verse for bounded `unsigned` integers.
- These measurements describe the existing reference without code modifications or speedup claims.

## Verification Command

```bash
python3 work/R20-T045/check.py
```

Expected final output line:

```text
RESULT: PASS - executed 5 cases
```
