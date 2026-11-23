# Hints

## General

- The target consists of three concentric circles centered at `(0, 0)`: inner circle radius `1` (`10` points), middle circle radius `5` (`5` points), and outer circle radius `10` (`1` point); landing outside radius `10` scores `0` points.
- Compute the Euclidean distance from `(0, 0)` using `std::hypot(x, y)` (from `<cmath>`), which computes $\sqrt{x^2 + y^2}$ without intermediate overflow/underflow.

## Walkthrough & Decision Table for Boundary Cases

### C++ Representation & Inclusive Boundaries

- **Parameter types:** `int score(float x, float y)` accepts `float` coordinates. When a test passes integer literals such as `-9`, `9`, `0`, `10`, or `-5`, C++ implicitly converts each `int` argument to `float` (`-9.0f`, `9.0f`, `0.0f`, `10.0f`, `-5.0f`).
- **Inclusive-boundary rule:** As specified in `.docs/instructions.md`, landing *in* a circle includes its outer perimeter (`distance <= 1`, `distance <= 5`, `distance <= 10`). Checking radii from innermost (`1`) to outermost (`10`) assigns the highest-scoring region containing `(x, y)`.

### Decision Table

| Case Name | Input `(x, y)` | Euclidean Distance `hypot(x, y)` | Rule from `instructions.md` | Result |
| :--- | :--- | :--- | :--- | :---: |
| `missed_target` | `(-9, 9)` | `sqrt(162) ~ 12.73` (`> 10`) | Outside target (`distance > 10`) -> `0` points | `0` |
| `on_the_outer_circle` | `(0, 10)` | `10` (`<= 10`, inclusive) | Outer circle (radius `10`, inclusive) -> `1` point | `1` |
| `on_the_middle_circle` | `(-5, 0)` | `5` (`<= 5`, inclusive) | Middle circle (radius `5`, inclusive) -> `5` points | `5` |

### Walkthrough

1. **`missed_target` (`score(-9, 9) == 0`):** Both coordinates convert to `float`. Distance is $\sqrt{(-9)^2 + 9^2} = \sqrt{162} \approx 12.7279 > 10$, so the dart lies outside the target (`0` points).
2. **`on_the_outer_circle` (`score(0, 10) == 1`):** Distance is $\sqrt{0^2 + 10^2} = 10$. Because the outer circle boundary (`radius = 10`) is inclusive, `10 <= 10` holds and awards `1` point.
3. **`on_the_middle_circle` (`score(-5, 0) == 5`):** Distance is $\sqrt{(-5)^2 + 0^2} = 5$. Because the middle circle boundary (`radius = 5`) is inclusive, `5 <= 5` holds and awards `5` points.

## Unspecified behaviour

- The specification defines real Cartesian coordinates `x` and `y` and the four concentric scoring regions; it does **not** specify special handling for `NaN`, positive/negative infinity (`+inf`/`-inf`), subnormal `float` rounding, throwing exceptions, type coercion rules beyond standard C++ `float` parameters, or a mandatory branch-evaluation order when regions are disjoint. No extra exception, coercion, or ordering rule is imposed beyond the stated scoring contract.
