# The Springer

The first stones that start an arch.

A stone is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted stone. The first accepted stone may be either side. The beat advances on every line, accepted or rejected. The arch starts (draws) when each side has taken one stone. An off-beat stone, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

`python3 made/the-springer.py check` prints PASS.

Standard library only. Nothing is deleted from the record.
