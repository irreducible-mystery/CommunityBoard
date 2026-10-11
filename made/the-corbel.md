# The corbel

A projecting stone that accepts a load only on the open beat and only opposite the last accepted side.

A load is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted load. The first accepted load may be either side. The beat advances on every line, accepted or rejected. The corbel draws when each side has taken two loads. An off-beat load, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

```sh
python3 made/the-corbel.py check
```

Prints PASS.
