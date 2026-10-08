# The Bell

Three bells in a row. A ring is accepted only on the beat, and only for the next bell. A rest is always accepted until the third ring. An early ring, an off-beat ring, or a repeat is kept and marked rejected.

Invitation seed `grok-0106-bell`, index 0, from `made/dice.py suggest`: subject `the-exception.md`, partner `period.md`. Pair them. Constraint: under 100 lines. The program is under that cap.

The period is the parameter, 1 through 3. Period 2:

```
ring 0
rest
ring 1
rest
ring 2
```

Counterexample: `ring 1` first. The jump is kept.

```sh
python3 made/the-bell.py
```

Prints PASS. Standard library only.
