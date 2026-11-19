# Hints

## General

- The exercise requires calculating the exact calendar date of meetup events given a month, year, weekday, and schedule descriptor.
- Schedule descriptors include: `teenth`, `first`, `second`, `third`, `fourth`, and `last`.

## The "Teenth" Schedule Contract

A "teenth" day is defined as any day of the month whose numerical date ends with the suffix "-teen":
The eligible dates are strictly: **13th, 14th, 15th, 16th, 17th, 18th, and 19th**.
Because this window consists of exactly 7 consecutive calendar days, **every day of the week occurs exactly once** within the teenth interval of any given month.

## Input / Output Walkthrough for Anchor Cases

### 1. `monteenth_of_May_2013`
- **Inputs**: Month = `May`, Year = `2013`, Schedule = `monteenth` (Monday ending in -teen).
- **Calendar Analysis**:
  - May 1, 2013 fell on a Wednesday.
  - The Mondays in May 2013 were: May 6, May 13, May 20, May 27.
  - Evaluating against the teenth interval $[13, 19]$:
    - May 13 $\in [13, 19]$ and is a Monday $\implies$ **Match**.
- **Result**: `2013-05-13` (`boost::gregorian::date(2013, boost::gregorian::May, 13)`).

### 2. `monteenth_of_August_2013`
- **Inputs**: Month = `August`, Year = `2013`, Schedule = `monteenth`.
- **Calendar Analysis**:
  - August 1, 2013 fell on a Thursday.
  - The Mondays in August 2013 were: August 5, August 12, August 19, August 26.
  - Evaluating against the teenth interval $[13, 19]$:
    - August 12 $< 13$
    - August 19 $\in [13, 19]$ and is a Monday $\implies$ **Match**.
- **Result**: `2013-08-19` (`boost::gregorian::date(2013, boost::gregorian::Aug, 19)`).

### 3. `monteenth_of_September_2013`
- **Inputs**: Month = `September`, Year = `2013`, Schedule = `monteenth`.
- **Calendar Analysis**:
  - September 1, 2013 fell on a Sunday.
  - The Mondays in September 2013 were: September 2, September 9, September 16, September 23, September 30.
  - Evaluating against the teenth interval $[13, 19]$:
    - September 9 $< 13$
    - September 16 $\in [13, 19]$ and is a Monday $\implies$ **Match**.
- **Result**: `2013-09-16` (`boost::gregorian::date(2013, boost::gregorian::Sep, 16)`).

## Decision Table

| Case Identifier | Year | Month | Target Weekday | Valid Teenth Days | Selected Date | Expected Output |
|---|---|---|---|---|---|---|
| `monteenth_of_May_2013` | 2013 | May | Monday | 13, 14, 15, 16, 17, 18, 19 | 13 | `2013-05-13` |
| `monteenth_of_August_2013` | 2013 | August | Monday | 13, 14, 15, 16, 17, 18, 19 | 19 | `2013-08-19` |
| `monteenth_of_September_2013` | 2013 | September | Monday | 13, 14, 15, 16, 17, 18, 19 | 16 | `2013-09-16` |

## C++ Representation and Unspecified Behavior

- **Date Type**: Dates are represented using `boost::gregorian::date` from `<boost/date_time/gregorian/gregorian.hpp>`.
- **Methods**: Each schedule/day combination is exposed as a method on `meetup::scheduler`, for instance `meetup.monteenth()`.
- **Unspecified Behavior**:
  - The specification leaves dates outside the valid Gregorian calendar range or non-existent combinations unspecified (no custom exception hierarchy is required for teenth days, as exactly one teenth day always exists for every day of the week in every month).
  - No ordering or sorting requirement is imposed beyond returning the matching `boost::gregorian::date` object.
