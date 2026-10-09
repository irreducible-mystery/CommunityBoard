# The Cistern

A word ladder that only changes a letter on the beat.

Noise Lab seed `grok-1808-cistern`, index 0: a word ladder and a rhythm. Constraint: make a small example and a counterexample.

The ladder is COLD, CORD, CARD, WARD, WARM. A step is a word. It is accepted if it is on the ladder and differs from the last accepted word by exactly one letter, and only when the tick is on the beat (`tick % 2 == 0`). A hold, the same word again, is accepted off the beat. An off-beat change, a two-letter jump, or a word off the ladder stays and is marked rejected.

The example route is COLD, hold, CORD, hold, CARD, hold, WARD, hold, WARM. The counterexample is COLD then CORD on the next tick: the change is off the beat, so it stays and is rejected.

`python3 made/the-cistern.py` prints PASS. Standard library only.
