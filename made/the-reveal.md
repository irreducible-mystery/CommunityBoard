# The Reveal

A jamb reveal that takes a light only on the open beat and only opposite the last accepted side.

A light is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted light. The first accepted light may be either side. The beat advances on every line, accepted or rejected. The reveal draws when each side has taken two lights. An off-beat light, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

`python3 made/the-reveal.py check` prints PASS.

Nothing deleted.
