# The hollow

A memory and an empty space, from Noise Lab invitation `grok-1507-stile`, index 0.
A small example and a counterexample.

Five cells start empty. `leave NAME i` is accepted only into an empty cell.
`take i` empties a held cell and remembers the name. A wait holds the room.
Leaving into a held cell, or taking an empty cell, stays and is marked rejected.

The example leaves `a` and `b`, takes `a` (that is the memory), and leaves `c` in the cell `a` left.
The counterexample leaves `b` onto `a` and takes an empty cell; both stay rejected, and nothing is remembered.

```sh
python3 made/the-hollow.py
```

Standard library only. Reads nothing else. Writes nothing.
