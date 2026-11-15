# Hints

## Why can a count of one be omitted?

Each encoded run records its character, and includes a count only when the run has more than one character. Try the one-character input `A`: the encoded result is `A`, not `1A`. Checking this boundary can help find an off-by-one condition when deciding whether to write a count.
