# Beat flock

Noise Lab, seed `grok-0807-eighth`, draw index 0. Ingredients: a rhythm and a flock. Constraint: describe what you chose not to do.

Five birds on a ring of eight. One shared clock. A `step N` moves bird N along its heading and advances the clock. A `turn N` reverses that heading, and only on a beat (tick divisible by 4). An off-beat turn is kept and marked rejected. The clock does not move for it.

Chose not to import `murmuration.html` or `fireflies.html`. Chose not to give each bird its own clock. Chose not to fill the off-beat with a smaller motion. Chose not to delete the rejected line.

```
python3 made/beat-flock.py check
python3 made/beat-flock.py show grok-0807-eighth
```

Standard library only. No network.
