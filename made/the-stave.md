# The Stave

A word ladder written as bars. Seed `grok-0305-ford`, invitation index 0:
a word ladder and a rhythm. Constraint: a small example and a counterexample.

The ladder is COLD–CORD–CARD–WARD–WARM. The parameter is the meter, 2 through 4.
A letter may change only on the first beat of a bar. The other beats hold the word.
A wrong line is kept and marked rejected.

Example: meter 3, fifteen notes, the ladder finishes.
Counterexample: CORD on the second beat is kept and rejected. A jump from COLD to WARM is kept and rejected.

```
python3 made/the-stave.py
```

Standard library only. Nothing deleted.
