# Quiet Stone

A five-by-five board for two players who never share a clock. Open `quiet-stone.html`
in a browser. No dependencies, no network.

## Rules

The board starts empty. Players alternate. A move is a column and a row, `a1` through `e5`,
`a1` at the top left. The first player is Light, the second is Dark.

A stone stays where it is put. Nothing is captured and nothing is removed. The game ends
when one cell is empty. That cell is the quiet stone. It scores for the player who would
have moved next, if and only if the number of orthogonal neighbours that are the other
player's stones is even (0, 2, or 4). Otherwise it scores for the player who just moved.
A corner has two neighbours, an edge three, the centre four.

There is no draw in the scoring rule. The empty cell is the whole prize.

## A move on the board

```
quiet-stone QS-20261005-first
light: c3
dark: c2
```

Replay with the page (paste the lines) or with the checks printed on load. A line that
names a filled cell or a cell off the board is kept and marked rejected. The original
placement stays.

The open round is `QS-20261005-first`. Light has not moved.
