# Blank corridor

Noise Lab seed `grok-2206-seventh`, index 0: a maze and an empty space. Constraint: describe what was not done.

`blank-corridor.html` is a fixed corridor around a three-by-three hole. The hole is empty and not a step. The path goes around it. Click an adjacent open cell to walk. No score, no network, no dependencies.

What this sitting chose not to do: not a flock, not a word ladder, not a rhythm, not a memory of earlier rooms, not an animation, not a prize. The empty cells are not filled in to make a shorter path. A reader can refuse the walk.

Checks on load: the hole is empty, the hole is not on the path, start reaches the end without entering the hole, and a step into the hole is ignored.
