# Maintenance: parallel-letter-frequency

## Overview
- Exercise: `exercises/practice/parallel-letter-frequency`
- Task: R20-T027
- Contribution: Language-specific hints for C++ const references and standalone micro-example with contrasting expression and pitfall explanation.

## Language Construct Analysis
1. **Const References (`const&`)**:
   - Signature: `std::unordered_map<char, size_t> frequency(std::vector<std::string_view> const& texts);`
   - Role: Avoids copying the collection of input texts ($O(N)$ allocation savings) while specifying read-only access semantics.
   - Relevance: Multiple concurrent execution tasks safely read from the vector without synchronization, provided data is not concurrently modified.
2. **Pitfall Addressed**:
   - Aliasing and lack of snapshot isolation when holding `const&`: `const` prevents mutation through the reference itself, but does not prevent mutations via the owner or other non-const aliases.
3. **Micro-example Outputs**:
   - Expression 1 (direct const ref): `3`
   - Expression 2 (after source mutation): `0`
