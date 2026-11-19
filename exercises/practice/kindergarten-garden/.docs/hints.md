# Hints

## General

- Students are arranged alphabetically: Alice is index 0, Bob is index 1, Charlie is index 2, and so forth.
- Each student is assigned 4 plant cups arranged as a $2 \times 2$ grid: two adjacent cups in the first (top) row and two adjacent cups directly beneath them in the second (bottom) row.
- The return value must be a collection or array of 4 `Plants` in order:
  1. Top-row, left cup
  2. Top-row, right cup
  3. Bottom-row, left cup
  4. Bottom-row, right cup

## Mapping Students to the 2x2 Cup Grid

Because each student owns two adjacent cups per row, a student at alphabetical position $k$ (0-indexed) starts at column $2k$.

Consider a 2-student garden with Alice ($k = 0$) and Bob ($k = 1$):

```text
Diagram: "VVCG\nVVRC"

Row 1 (indices 0..3):     V  V  C  G
                          -  -  -  -
Index:                    0  1  2  3
Student:                 [ Alice ][  Bob  ]

Newline character:        \n (at index 4)

Row 2 (indices 5..8):     V  V  R  C
                          -  -  -  -
Index:                    5  6  7  8
Student:                 [ Alice ][  Bob  ]
```

### Diagnostic Trace for Bob ($k = 1$):
- Offset from the start of each row: $2 \times 1 = 2$.
- Top row positions:
  - Cup 1: Index `2` $\rightarrow$ `'C'` (`Plants::clover`)
  - Cup 2: Index `2 + 1 = 3` $\rightarrow$ `'G'` (`Plants::grass`)
- Bottom row starts after the newline character (`diagram.find('\n') + 1`):
  - Row 2 base index is `5`.
  - Cup 3: Index `5 + 2 = 7` $\rightarrow$ `'R'` (`Plants::radishes`)
  - Cup 4: Index `5 + 2 + 1 = 8` $\rightarrow$ `'C'` (`Plants::clover`)

Result for Bob: `{clover, grass, radishes, clover}`.
