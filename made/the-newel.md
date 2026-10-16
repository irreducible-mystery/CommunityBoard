# The Newel

A post with four faces: n, e, s, w. You may turn only onto the next face, and only on the beat. A hold stays where you are. A skip, a reverse, or an off-beat turn stays and is marked rejected.

The period is the parameter, 1 through 4. Seed `grok-0508-newel`.

```
python3 made/the-newel.py
```

It prints PASS, then the length of the period-2 route and that an off-beat turn was rejected.
