# The Ember

A flock and a rhythm. Noise Lab seed `grok-1305-ember`, index 0. The invitation was accepted.

Three birds, `a` `b` `c`, start on seats 0, 2, and 4 of a ring of six. A line is `step NAME SEAT` or `rest`. The parameter a reader can change is the period, clamped to 1..4. A step lands only on the beat, and only on a free seat. A rest is only off the beat. A line that breaks a rule stays and is marked rejected.

`python3 made/the-ember.py` prints PASS. No dependencies.
