# The Eave

An empty porch and a rhythm, for a reader who is not on a network.

Companion to [`the-eave.py`](the-eave.py).
Grok, 2026-10-08 04:08 UTC, from a Noise Lab invitation (seed `grok-0407-eave`, index 0):
combine a rhythm and an empty space, and make it work without a network.

## Rules

Four cells. The middle is empty and is not a cell. A line is `wait` or `step N`.
A step lands only in an empty index, and only when the beat is a multiple of the period.
The parameter a reader may change is the period, 1 through 4. A miss is kept and marked rejected.

Example, period 2: step 0, wait, step 1, wait, step 2, wait, step 3.
Counterexample: `step 1` immediately after `step 0` is off the beat, kept, and rejected.

`python3 made/the-eave.py` prints PASS.
