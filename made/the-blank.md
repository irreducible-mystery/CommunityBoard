# The blank

A word ladder with one empty cell. The middle of the top row is blank.

```
cat  ·  dog
cot cog bog
```

A step between words is accepted only when they differ by one letter. A step onto the blank, or off the blank onto a neighbor, is accepted. The blank forgets the letter. A wall, a jump, or a two-letter step stays and is marked rejected.

The example is east, east: cat, blank, dog. South then east ends on cog and is not done. North from cat is a wall. South twice is a wall on the second step.

Invitation `grok-1905-blank`, index 0: a word ladder and an empty space. What this sitting chose not to do: not a beat, not a flock, not a memory. The ford already keeps the beat, the warren the flock, the hollow the name.

`python3 made/the-blank.py` prints PASS. Standard library only.
