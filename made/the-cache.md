# The cache

An empty cell between two words. From Noise Lab invitation `grok-2208-sill`, index 0: an empty space and a memory. At most 100 lines.

The row is `cold`, empty, `warm`. A step from a word into the empty cell is accepted and does not change the memory. A step off the empty cell is accepted only onto the word it remembers, or onto either neighbor while the memory is blank. Entering a word while the memory is blank writes that word. A wall, a bad line, or a mismatch stays and is marked rejected.

Right, right crosses and is done: the memory is `warm`. Right, right, left returns to the empty cell; the next left is rejected, because `cold` is not what the cell remembers. Right, left returns to `cold` and is not done.

`python3 made/the-cache.py` prints PASS. Standard library only.
