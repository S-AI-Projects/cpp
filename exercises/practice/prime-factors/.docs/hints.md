# Hints

## Start with the contract examples

The result is a `std::vector<long long>` containing the prime factors. The selected cases make the empty result and the one-factor results concrete:

| Input | Why | Expected vector |
| --- | --- | --- |
| `1` | The instructions explicitly say that 1 is not prime, so it has no prime factors. | `{}` |
| `2` | 2 is prime, so its only prime factor is itself. | `{2}` |
| `3` | 3 is also prime, so its only prime factor is itself. | `{3}` |

The examples are vectors, including the empty vector for input `1`; they are not error values. Since the last two vectors each contain one item, these cases do not distinguish any ordering rule. The instructions' worked example for `60` lists the divisors it finds as `2, 2, 3, 5`.

The exercise describes a natural-number input. It does not define a result, exception, or coercion for values outside that contract, such as a negative input. Do not infer extra error behavior from the C++ parameter type `long long`.
