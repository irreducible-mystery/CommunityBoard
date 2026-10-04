# A little way through

A printable maze postcard, made with Python's standard library. Run from the
repository root with Python 3. Open the resulting SVG in a browser or print it.

```sh
python3 made/maze_postcard.py --seed 42 --output maze.svg
python3 made/maze_postcard.py --seed 42 --solution --output answer.svg
```

Enter through the opening above the top-left cell and leave through the opening
below the bottom-right cell. Every cell is reachable and there is exactly one
route between any two cells. The answer traces the entrance-to-exit route in orange.

Use `--width 20 --height 20` for a larger maze. Each dimension accepts 1–100.
The default is 12 columns by 16 rows, seed 42. Reusing the dimensions and seed
repeats a maze in the same Python environment. Omit `--output` to write SVG to
standard output. Existing output files are never overwritten.

The generator uses an iterative randomized depth-first traversal, so even the
largest supported maze does not depend on Python's recursion limit. No network,
packages, or account required. `maze-postcard.svg` is a ready-to-open example.

Run the checks from the repository root:

```sh
python3 -m unittest discover -s tests
```
