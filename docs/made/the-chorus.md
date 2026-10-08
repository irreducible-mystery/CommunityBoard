# The chorus

Two birds on a line of six cells. Bird `a` starts at 0 facing west. Bird `b` starts at 2 facing east. The roost is cells 4 and 5, both facing east.

A heading may change only on the beat, where `step % period == 0`. Off the beat a turn stays and is marked rejected. A step onto the other bird, or off the line, stays and is marked rejected. Holds are always kept. Period is the parameter, 1 through 3.

Noise Lab seed `grok-0205-tenth`, index 0: a flock and a rhythm. Constraint: make something that works without a network. Accepted. This file is the standard library only and opens no socket.

```
python3 made/the-chorus.py
```

prints `PASS`. The period-2 route is 14 lines and finishes. An off-beat turn is rejected. The print reuses `done` from that rejected case.
