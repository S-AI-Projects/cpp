# Clock Exercise Hints

## Approach Selection: Two Ways to Represent Time

This exercise has more than one valid way to represent and manipulate time.
Understanding the trade-offs helps you choose the right approach.

### Approach 1: Separate Hour and Minute (Reference)

**Representation:** Two integers `hour_` and `minute_` (0-23 and 0-59)

**Pros:**
- Intuitive: matches how humans think about time
- Direct access to hour and minute components
- Easy to debug (inspect `hour_` and `minute_` separately)

**Cons:**
- Requires a `clean()` method to normalize after each operation
- Complex negative-value handling with borrowing logic
- More code, more edge cases

**Example:**
```cpp
// 10:00 + 90 minutes = 11:30
clock::at(10, 0).plus(90)  // hour_ becomes 11, minute_ becomes 30
```

### Approach 2: Total Minutes Since Midnight (Alternative)

**Representation:** Single integer `total_minutes_` (0-1439)

**Pros:**
- Simpler logic: just add/subtract and modulo 1440
- No complex `clean()` method needed
- Less code, fewer edge cases
- Easy to reason about: `total_minutes_` uniquely identifies any time

**Cons:**
- Must convert to hours/minutes for display
- Less intuitive for debugging (what is minute 840?)

**Example:**
```cpp
// 10:00 = 600 minutes, +90 = 690 minutes = 11:30
clock::at(10, 0).plus(90)  // total_minutes_ = 690
// Display: 690 / 60 = 11 hours, 690 % 60 = 30 minutes
```

### Trade-off Summary

| Aspect | Separate Hour/Minute | Total Minutes |
|--------|---------------------|---------------|
| Code complexity | Higher (clean() logic) | Lower (simple modulo) |
| Memory | 2 ints | 1 int |
| Debugging | Easier (readable state) | Harder (opaque number) |
| Display cost | O(1) | O(1) (division) |
| Operation cost | O(1) with normalization | O(1) without normalization |

**Recommendation:** Use the total-minutes approach for simpler code. Use separate hour/minute when you need frequent component access or want more readable debug output.