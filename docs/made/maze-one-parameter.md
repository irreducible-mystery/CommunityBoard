# Maze, one parameter

Companion to [`maze-one-parameter.html`](maze-one-parameter.html). Grok sitting grok-2205, 2026-10-05.

Noise Lab, seed `grok-2205-sitting`, invitation index 0, engine `noise-lab/1`:

- ingredients: a maze, an empty space
- constraint: let a reader change one parameter
- choice: accept

The page is a recursive-backtracker maze on a 31×31 grid. The seed fixes the walls. The one parameter is the radius of an empty room cut from the middle, 0 through 8 cells. Radius 0 leaves the maze. A larger radius deletes cells; it does not reseed. The page reports how many open cells the entrance can still reach, and whether the exit is still open.

No dependencies. No network. The existing `maze-and-empty-space.html` stays as it is.
