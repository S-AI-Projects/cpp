# Flower Field Exercise Maintenance

This document provides maintenance notes and mapping for canonical test cases in `exercises/practice/flower-field/.meta/tests.toml`.

## Canonical Case Mapping Table

| UUID | Description | C++ Rationale / Coverage Notes |
|---|---|---|
| `237ff487-467a-47e1-9b01-8a891844f86c` | no rows | Validates empty grid input (`std::vector<std::string>{}`), ensuring zero rows produces an empty result vector without boundary issues. |
| `4b4134ec-e20f-439c-a295-664c38950ba1` | no columns | Validates single row with zero columns (`""`), ensuring correct handling of empty string elements. |
| `d774d054-bbad-4867-88ae-069cbd1c4f92` | no flowers | Validates grid containing only spaces (`"   "`), ensuring space-only input produces expected unannotated grid. |
