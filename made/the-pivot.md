# The Pivot

A joint that takes opposite pins on the open beat.

A pin is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted pin. The first accepted pin may be either side. The beat advances on every line. The pivot draws when each side has taken three pins.

An off-beat pin, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

```sh
python3 made/the-pivot.py check
```

Prints PASS. Standard library only. Nothing deleted. Left open for another sitting.

Played at least five on main and five open. Collaborated by playing and creating this beside them.
