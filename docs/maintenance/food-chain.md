# Food-chain reference cost

## Fixed input domain

The exercise has eight valid verse numbers (`1` through `8`), so there is no unbounded input size to benchmark. `song_verse::sing()` is called once for a valid verse and concatenates its fixed lyric fragments. For verses `1` through `7`, the builder appends one prior verse fragment per loop iteration; the terminal horse verse (`8`) skips that cumulative loop. Each `song_verse::verse()` returns one fixed fragment by value. The underlying string work is proportional to the number of characters copied, but the table bounds those lengths and the loop count.

The operation counts below were collected from an instrumented temporary copy after the unmodified reference passed all 10 enabled tests. Counts are method calls and prior-fragment appends, not machine instructions or timings. They describe only verse-building work and exclude process startup, compilation, and test-runner overhead.

| Valid verse input | `song_verse::sing()` calls | `song_verse::verse()` calls | Prior-fragment appends | Loop-condition checks |
|---:|---:|---:|---:|---:|
| 1 (fly) | 1 | 0 | 0 | 1 |
| 2 (spider) | 1 | 1 | 1 | 2 |
| 3 (bird) | 1 | 2 | 2 | 3 |
| 4 (cat) | 1 | 3 | 3 | 4 |
| 5 (dog) | 1 | 4 | 4 | 5 |
| 6 (goat) | 1 | 5 | 5 | 6 |
| 7 (cow) | 1 | 6 | 6 | 7 |
| 8 (horse) | 1 | 0 | 0 | 0 |

Thus the largest valid cumulative verse executes six prior-fragment copies; the horse verse is a fixed terminal case. The full-song interface calls `verse()` for each of the eight valid numbers, with nested work still bounded by this table. These counts describe this fixed table, and do not support claims about timing or about an unbounded, generalized song.

Reproduce the reference test and operation-count check with `python3 work/R20-T015/check.py` from the task workspace. The check copies dotfiles, maps the configured reference to the learner paths only in a temporary directory, builds and runs the exercise tests, then measures the fixed-domain method calls in an instrumented temporary source copy. It does not modify the learner files.
