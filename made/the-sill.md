# The Sill

A word ladder with one held note. Noise Lab seed `grok-1607-sill`, index 0:
a rhythm and a word ladder. Constraint: a small example and a counterexample.

The ladder is COLD–CORD–CARD–WARD–WARM. A beat changes one letter. A rest
changes none. The parameter is which rung is held, 0 through 4. A wrong line
stays and is marked rejected.

Example, rest after CORD:

```
COLD
CORD
CORD
CARD
WARD
WARM
```

Counterexample: `CARD` where the beat asked for `CORD`. Two letters move at
once. The line is kept.

```sh
python3 made/the-sill.py check
```

Prints `PASS`. No dependencies.
