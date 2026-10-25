# The ford

A word ladder and a maze, from Noise Lab invitation `grok-0510-eleventh`, index 0.
The reader changes one parameter: the period, 1, 2, or 3.

The stones are `cold cord card ward warm`. A step changes one letter onto the next
word, and only when the step index is divisible by the period. A wait holds the
word. A jump, a two-letter change, or an off-beat step stays and is marked rejected.

```sh
python3 made/the-ford.py
```

Standard library only. Reads nothing else. Writes nothing.
