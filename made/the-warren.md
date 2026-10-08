# The Warren

A maze and a flock. Noise Lab seed `grok-2308-eighth`, index 0. Ingredients: a maze, a flock. Constraint: keep one assumption visible and change another.

The assumption kept visible: birds still separate. A step onto an occupied cell is kept and marked rejected. The bird does not move.

The assumption changed: walls block steps, not headings. Alignment looks through the wall. The same seed with headings stopped by walls is the counterexample. That flock does not reach the far room.

Three rooms, west, middle, east. Doors only between neighbors. Three birds. Standard library only.

```sh
python3 made/the-warren.py
```

prints PASS.
