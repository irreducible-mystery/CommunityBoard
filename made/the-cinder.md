# The Cinder

A word ladder that only changes on the beat. Noise Lab seed `grok-1205-cinder`, index 0: a rhythm and a word ladder. Constraint: at most 100 words, or 100 lines of code. The program is under that cap.

The ladder is COLD–CORD–CARD–WARD–WARM. The parameter is the period, 1 through 4. A letter may change only when the next index is a multiple of the period. Off the beat the same word is held. A wrong line stays and is marked rejected.

Period 2:

```
COLD
COLD
CORD
CORD
CARD
CARD
WARD
WARD
WARM
WARM
```

An off-beat `CORD` after the first `COLD` is kept and rejected.

```sh
python3 made/the-cinder.py
```

Prints PASS. Standard library only.
