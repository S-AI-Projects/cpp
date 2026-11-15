# Run-length encoding maintenance notes

## Single-character run boundary

The encoding contract leaves a run's count out when that run contains exactly one character. The reference implementation follows this rule when it flushes a run and when it writes the final run.

For mutation testing, changing the count condition from `counter > 1` to `counter >= 1` at both output points is a deliberate mutant. The existing case `encode single characters only are encoded without count` (canonical test ID `52012823-b7e6-4277-893c-5b96d42f82de`) rejects it: input `XYZ` should produce `XYZ`, while the mutant produces `1X1Y1Z`. The smallest non-empty diagnostic input is `A`; the expected output is `A`, and the mutant produces `1A`. The empty-string case still passes, so the one-character case is the shortest input that distinguishes this mutant.

The current suite already covers this boundary, so no additional canonical test is proposed. The mutation and both implementations are exercised in an isolated copy by `python3 work/R20-T013/check.py`.
