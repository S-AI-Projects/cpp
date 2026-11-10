# Clock Exercise Maintenance

This document provides comparison of two clock implementations in `exercises/practice/clock/`.

## Two Approaches to Clock Representation

### Approach 1: Separate Hour and Minute (Reference)

**File:** `exercises/practice/clock/.meta/example.cpp`

**Representation:** Two member variables `hour_` (0-23) and `minute_` (0-59)

**Key operations:**
```cpp
void clock::clean() {
    if (minute_ < 0) {
        int tmp = 1 + (minute_ / -minutes_per_hour);
        hour_ -= tmp;
        minute_ += minutes_per_hour * tmp;
    }
    if (hour_ < 0) hour_ += hours_per_day * (1 + (hour_ / -hours_per_day));
    hour_ += minute_ / minutes_per_hour;
    hour_ %= hours_per_day;
    minute_ %= minutes_per_hour;
}
```

**Complexity:** O(1) per operation, but with more branching and edge cases

### Approach 2: Total Minutes Since Midnight (Alternative)

**Representation:** Single member variable `total_minutes_` (0-1439)

**Key operations:**
```cpp
clock& clock::plus(int minutes) {
    total_minutes_ = (total_minutes_ + minutes) % minutes_per_day;
    if (total_minutes_ < 0) total_minutes_ += minutes_per_day;
    return *this;
}
```

**Complexity:** O(1) per operation, simpler logic, fewer branches

## Comparison Results

Both implementations pass all 50 test cases:
- `time_tests`: 17 cases (time display and rollover)
- `add_tests`: 16 cases (addition and subtraction)
- `equal_tests`: 17 cases (clock equality)

**Trade-off:**
- **Separate hour/minute**: More readable debug state, but more complex `clean()` logic
- **Total minutes**: Simpler code, less branching, but opaque internal state

**Recommendation:** The total-minutes approach is preferred for its simplicity. The separate approach is useful when component access is frequent.