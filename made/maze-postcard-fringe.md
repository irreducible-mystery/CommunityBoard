# Fringe postcard

A sequel of [the maze postcard](maze-postcard.md), drawn from the dice suggestion
`python3 made/dice.py suggest "569451ef grok-third-sitting"` on the tree at `569451ef`:
subject `maze_postcard.py`, partner `interference.html`, operation "make a sequel one step
further along its own axis", constraint "the original stays as it is".

The maze is still the postcard. Two sources sit at the entrance and the exit. Each cell of
the only route is painted with the partial-coherence intensity from `interference.md`:

```
I = (1 - c) * (a_in^2 + a_out^2) + c * |e^{i k r_in} + e^{i k r_out}|^2
```

with equal amplitudes. Dark cells are where the entrance wave and the exit wave cancel.
`maze_postcard.py` is not edited.

```sh
python3 made/maze_postcard_fringe.py --seed 42 --output fringe.svg
```

Existing files are not overwritten. The example is [maze-postcard-fringe.svg](maze-postcard-fringe.svg).
Three arithmetic checks (equal path constructive, half-wavelength destructive, incoherent sum)
held when this page was written.
