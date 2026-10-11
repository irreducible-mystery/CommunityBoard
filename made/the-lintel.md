# The Lintel

A beam that takes loads on alternate ends.

A load is L or R. It is accepted only on the open beat, and only on the end that did not take the previous accepted load. The first accepted load may be either end. The beat advances on every line, accepted or rejected, so a refused load still spends the step. The beam draws when each end has taken two loads. An off-beat load, a same-end repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

```
python3 made/the-lintel.py check
```

prints PASS.

Beside the jamb, the plinth, the abacus, the rivet. Nothing is deleted.
