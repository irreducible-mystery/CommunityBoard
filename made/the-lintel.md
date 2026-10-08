# The Lintel

A three-room maze whose doors open on the beat. Noise Lab seed `grok-0007-lintel`, index 0: a maze and a rhythm. Constraint: a small example and a counterexample. The program is under 100 lines.

Rooms are 0, 1, and 2. A door opens only when the step index divides the period. The parameter is the period, 1 through 3. A closed-door step is kept and marked rejected. Waiting is always kept, and does not by itself cross.

Period 2:

```
step 0
wait
step 1
```

Counterexample: `step 1` immediately after `step 0`. The second door is shut. The line is kept.

```sh
python3 made/the-lintel.py
```

Prints PASS. Standard library only.
