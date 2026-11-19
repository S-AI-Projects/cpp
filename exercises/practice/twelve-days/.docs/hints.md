# Hints

## General

- Pay close attention to how gifts are joined across different verses:
  - In verse 1, there is only a single gift, so no conjunction is used:
    `"a Partridge in a Pear Tree."`
  - In verses 2 through 12, each earlier gift is listed in reverse order, and the final gift is preceded by `", and "`:
    `"... two Turtle Doves, and a Partridge in a Pear Tree."`
- If verse 1 passes (`twelve_days::recite(1, 1)`) but verse 2 fails (`twelve_days::recite(2, 2)`), check whether your verse-joining logic mistakenly uses `", "` instead of `", and "` before `"a Partridge in a Pear Tree"` when more than one gift is present.
