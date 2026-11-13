# Yacht Exercise Maintenance

This document provides complexity analysis for the reference implementation in `exercises/practice/yacht/.meta/example.cpp`.

## Complexity Analysis: `simple_scores`

### Function Signature
```cpp
int simple_scores(const std::array<int, 5>& dice, int target);
```

### Input Size Definition
The input size is **fixed** by the exercise domain:
- Always exactly 5 dice (array size = 5)
- Each die value is in range [1, 6]
- Target is in range [1, 6]

This is a **fixed-domain exercise** - no variable input size exists.

### Algorithm Analysis
```cpp
return std::accumulate(
    dice.begin(), dice.end(), 0,
    [target](int acc, int i) { return i == target ? acc + i : acc; });
```

**Operations per call (exact count):**
- 5 iterations (one per die)
- 5 comparisons (`i == target`)
- 0-5 additions (`acc + i`) depending on matches
- 5 lambda invocations

**Total: O(1) - constant time and space**

### Cost Statement
The `simple_scores` function executes in **constant time O(1)** with exactly **5 iterations** and **5 comparisons** per call, regardless of input values. Since the dice array is always size 5 (the game uses exactly 5 dice), there is no scaling behavior to measure across input sizes.

The cost is dominated by:
1. Function call overhead
2. Loop overhead (5 iterations)
3. 5 integer comparisons
4. Up to 5 integer additions (when dice match target)

This is a fixed-domain exercise; the "input size" is always 5 dice. No benchmark across varying sizes is applicable - the domain is fixed by the rules of Yacht.

### Measurement Context
- **Algorithm work**: ~5-10 CPU cycles per call (trivial)
- **Process startup**: ~1-10ms (dominates any measurement)
- **Compilation time**: ~100-500ms (one-time)

For such a trivial fixed-size operation, microbenchmarking is not meaningful. The complexity is analytically O(1) with exactly 5 loop iterations.

## Automated Check

Run the check:
```bash
python3 work/R20-T035/check.py
```