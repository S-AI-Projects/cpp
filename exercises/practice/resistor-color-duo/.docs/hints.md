# Hints

## General

- The goal is to take an ordered collection of color band names and encode the first two bands into a two-digit integer resistance value: `tens * 10 + units`.
- Any colors beyond the first two must be ignored (e.g. `{"green", "brown", "orange"}` yields `51`).

## Approach Selection

In C++, there are two idiomatic approaches to map color names to their numerical values ($0$ through $9$):

### Approach 1: Sequential Vector / Array Index Search (`std::find`)

Store the color names in order in a fixed sequence where the index directly corresponds to the resistor code:

```cpp
#include <algorithm>
#include <string>
#include <vector>

namespace resistor_color_duo {

const std::vector<std::string> colors{
    "black", "brown", "red", "orange", "yellow",
    "green", "blue", "violet", "grey", "white"
};

int color_code(const std::string& color) {
    auto it = std::find(colors.begin(), colors.end(), color);
    return (it != colors.end()) ? std::distance(colors.begin(), it) : -1;
}

int value(const std::vector<std::string>& bands) {
    return color_code(bands[0]) * 10 + color_code(bands[1]);
}

}
```

- **Data Representation**: Flat continuous array/vector of 10 elements.
- **Trade-offs**:
  - Memory: Minimum memory footprint and optimal cache locality (single contiguous buffer).
  - Time: Linear scan $\mathcal{O}(K)$ where $K = 10$. Because $K$ is tiny ($10$ elements), a linear scan with CPU cache prefetching is exceptionally fast and often beats hash lookups in practice.

### Approach 2: Associative Lookup (`std::unordered_map` or `std::map`)

Store explicit key-value mappings from color strings to integers:

```cpp
#include <string>
#include <unordered_map>
#include <vector>

namespace resistor_color_duo {

const std::unordered_map<std::string, int> color_map{
    {"black", 0}, {"brown", 1}, {"red", 2},    {"orange", 3}, {"yellow", 4},
    {"green", 5}, {"blue", 6},  {"violet", 7}, {"grey", 8},   {"white", 9}
};

int value(const std::vector<std::string>& bands) {
    return color_map.at(bands[0]) * 10 + color_map.at(bands[1]);
}

}
```

- **Data Representation**: Hash table (`std::unordered_map`) or red-black binary search tree (`std::map`).
- **Trade-offs**:
  - Memory: Dynamic node allocations and bucket table overhead per entry.
  - Time: $\mathcal{O}(1)$ average lookup time per band. Highly readable and expressive syntax, but carries constant-factor hashing and pointer indirection overhead.

### Worked Example

- **Input**: `{"brown", "black"}`
  - Band 0: `"brown"` $\to$ value $1$
  - Band 1: `"black"` $\to$ value $0$
  - Result: $1 \times 10 + 0 = 10$
- **Input**: `{"blue", "grey"}`
  - Band 0: `"blue"` $\to$ value $6$
  - Band 1: `"grey"` $\to$ value $8$
  - Result: $6 \times 10 + 8 = 68$
- **Input**: `{"white", "red"}`
  - Band 0: `"white"` $\to$ value $9$
  - Band 1: `"red"` $\to$ value $2$
  - Result: $9 \times 10 + 2 = 92$
