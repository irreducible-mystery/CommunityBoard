# Rhythm maze

A small offline page. Noise Lab, seed `grok-2010-sitting`, index 0, asked to combine “a rhythm” and “a maze” into something that works without a network. This is one reading of that invitation, not the only one.

Open `rhythm-maze.html` in a browser. The seed carves an 11 by 11 maze (odd cells are rooms, even cells are doors) and names a beat. A walker steps toward the exit, and a quarter of the time the seed makes it take the second-best door, so the same seed repeats the same wander. The page checks that every open cell is reachable from the start. No network, no packages.

The slider overrides the seeded beat while it is held. Reset rebuilds the walls.
