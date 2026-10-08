# The weir

A channel and a lip. Water rises one unit every step. A stone may be laid only on the beat, when the step index is divisible by the period. The period is the parameter, 1 through 3.

The weir holds if four stones are down before the rise passes the lip. Period 1 holds. Period 2 does not: water outruns the stones. An off-beat lay is kept and marked rejected. A line after the weir holds, or after it spills, is kept and marked rejected.

```
python3 made/the-weir.py
```

It prints PASS, then the period-1 route (held) and the period-2 route (the rise passed the lip).
