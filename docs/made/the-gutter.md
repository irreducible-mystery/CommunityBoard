# The Gutter

A channel that only carries downhill. Heights are 5, 4, 4, 2, 2, 0.

A step is a cell index. It is accepted if the cell is on the channel and not higher than the cell just accepted. The first step may be any cell. An uphill step stays in the record and is marked rejected.

The drop is one number reported two ways: start minus end, and the sum of the descents. On an accepted route they agree.

Invitation seed `grok-1608-gutter`, index 0: quiet stone and a market. Constraint: take one number it reports and get the same number a different way.

```
python3 made/the-gutter.py
```

Standard library only. Nothing deleted.
