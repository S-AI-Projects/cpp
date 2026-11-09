# Isogram Hints

## Debugging Hint: Case-Insensitive Comparison

When checking whether a word is an isogram (no repeated letters), remember that
**case does not matter**. The letters `A` and `a` are considered the same letter.

If your implementation seems to incorrectly report a word like `"Alphabet"` as an
isogram, double-check whether you are normalizing the case of each character
before comparing it against previously seen characters.

A minimal diagnostic input to test this behavior:
- Input: `"Alphabet"`
- Expected result: `false` (because `A` and `a` are the same letter)