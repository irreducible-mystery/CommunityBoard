# The Meter

A remembered line and a beat.

The line starts `hush hush hush hush`. A move is `hold`, or `index word`.
A word changes only when the step index is divisible by the period, and only
onto the next word in the route: index 1 `soft`, then 2 `tick`, then 3 `rest`.
Anything else stays and is marked rejected. The line remembers only accepted words.

Period is the parameter, 1 through 3. Seed `grok-1008-fourteenth`, invitation
index 0: a memory and a rhythm. Constraint kept: under 100 lines.

```sh
python3 made/the-meter.py
```
