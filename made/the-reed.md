# The Reed

A pipe that only changes pitch after a rest. Noise Lab seed `grok-2206-reed`, index 0: a rhythm and an empty space. Constraint: at most 100 lines. The program is under that cap.

The scale is A–C–E–G. The parameter is the rest, 1 through 3. A new pitch is accepted only after that many held notes. A change with no rest is kept and marked rejected.

Rest 1:

```
A
A
C
C
E
E
G
G
```

Counterexample: `C` after the first `A`. The jump is kept.

```sh
python3 made/the-reed.py
```

Prints PASS. Standard library only.
