# Hints

## Choose a representation for the clues

One option is to store five houses, each with its color, resident, pet, drink, and hobby, then check the clues by scanning neighboring houses. Another option is to store each category as positions: for example, `nationality[Norwegian]` is the zero-based house number of the Norwegian resident. A permutation of positions ensures that each category appears exactly once.

For a small worked clue, the Norwegian lives in the first house, so `nationality[Norwegian]` is `0`. Since the Norwegian lives next to the blue house, `color[Blue]` must be `1`. The green house immediately right of the ivory house can be written as `color[Green] == color[Ivory] + 1`.

Position arrays make relational clues and answer lookup direct, but require several small arrays and careful index-to-house reasoning. A per-house record groups all facts about one resident and can be easier to inspect, while expressing a relationship between two categories takes more scanning. Neither representation changes the need to satisfy every clue and keep category values distinct.
