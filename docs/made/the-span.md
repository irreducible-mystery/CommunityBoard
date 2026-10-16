# The Span

A footbridge across an empty gap. Noise Lab seed `grok-2105-span`, index 0:
an empty space and a ladder. Constraint: at most 100 lines.

The near bank counts as already laid. A line is a plank index. The parameter
is the length, 3 through 6. A plank is accepted only on an empty index next
to one already laid. A gap jump, or a second plank on a taken index, stays
and is marked rejected. The far bank is reached when every index is laid.

Example, length 4:

```
0
1
2
3
```

Counterexample: `2` before `1`. The gap is kept.

```sh
python3 made/the-span.py
```
