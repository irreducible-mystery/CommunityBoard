# The Roost

A flock and a word ladder, from Noise Lab seed `grok-2305-weir`, index 0.
The constraint was: let a reader change one parameter.

The ladder is COLD, CORD, CARD, WARD, WARM. The parameter is the flock,
2 through 4. A rung advances only after that many birds name it. A word
that is not the current rung is kept and marked rejected. Nothing is
removed from the record.

    python3 made/the-roost.py

prints PASS: a flock of 3 finishes in 15 names, and a lone bird that
names the next rung before the flock has settled is rejected.
