# Paper mazes

A small maze generator using only Python's standard library. Each maze has one
route between any two cells. Enter at the top left; exit at the bottom right.

From the repository root:

```sh
python3 made/maze.py --seed 42 > maze.svg
python3 made/maze.py --seed 42 --solution > solution.svg
python3 made/maze.py --width 30 --height 20 --seed 7 > large-maze.svg
```

Open the SVG in a browser to view or print it. Use the same dimensions and seed
to reproduce a puzzle and its answer. Omit the seed for a new random maze.
Dimensions range from 1 to 100 cells on each side. No network or packages needed.

The generator uses iterative randomized depth-first search, removing walls only
when it reaches an unvisited cell. This makes a connected maze without loops.
The optional solution follows the cell connections from entrance to exit.

Run the checks with `python3 -m unittest discover -s tests -p 'test_maze.py'`.
