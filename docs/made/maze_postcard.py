#!/usr/bin/env python3
"""Make a printable maze SVG. Uses only the Python standard library."""

import argparse
from collections import deque
from html import escape
from pathlib import Path
import random
import sys


def make_maze(width, height, seed):
    """Return a connected, acyclic graph of cells, using iterative DFS."""
    if not (1 <= width <= 100 and 1 <= height <= 100):
        raise ValueError("width and height must be between 1 and 100")
    rng = random.Random(seed)
    passages = {i: set() for i in range(width * height)}
    seen = {0}
    stack = [0]
    while stack:
        cell = stack[-1]
        x, y = cell % width, cell // width
        choices = [ny * width + nx for nx, ny in
                   ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y))
                   if 0 <= nx < width and 0 <= ny < height
                   and ny * width + nx not in seen]
        if not choices:
            stack.pop()
            continue
        nxt = rng.choice(choices)
        passages[cell].add(nxt)
        passages[nxt].add(cell)
        seen.add(nxt)
        stack.append(nxt)
    return passages


def solve(passages):
    """Return the path from the first cell to the last."""
    goal = len(passages) - 1
    parents = {0: None}
    queue = deque([0])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            path = []
            while cell is not None:
                path.append(cell)
                cell = parents[cell]
            return path[::-1]
        for nxt in sorted(passages[cell]):
            if nxt not in parents:
                parents[nxt] = cell
                queue.append(nxt)
    raise ValueError("maze has no route to the exit")


def render_svg(width, height, seed, solution=False):
    passages = make_maze(width, height, seed)
    unit, left, top = 24, 40, 90
    page_w, page_h = max(360, width * unit + 80), height * unit + 156
    label = escape(str(seed))
    lines = []

    def wall(x1, y1, x2, y2):
        lines.append(f'M{left + x1 * unit},{top + y1 * unit}'
                     f'L{left + x2 * unit},{top + y2 * unit}')

    for cell in passages:
        x, y = cell % width, cell // width
        if y == 0 and cell != 0:
            wall(x, y, x + 1, y)
        if x == 0:
            wall(x, y, x, y + 1)
        if x == width - 1 or cell + 1 not in passages[cell]:
            wall(x + 1, y, x + 1, y + 1)
        if (y == height - 1 and cell != width * height - 1) or (
                y < height - 1 and cell + width not in passages[cell]):
            wall(x, y + 1, x + 1, y + 1)
    route = ""
    if solution:
        points = [(left + unit / 2, top - 9)]
        points += [(left + (c % width + .5) * unit,
                    top + (c // width + .5) * unit) for c in solve(passages)]
        points.append((left + (width - .5) * unit, top + height * unit + 9))
        coords = " ".join(f"{x},{y}" for x, y in points)
        route = f'<polyline points="{coords}" fill="none" stroke="#c55a39" stroke-width="3"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{page_w}" height="{page_h}"
 viewBox="0 0 {page_w} {page_h}" role="img" aria-labelledby="title desc">
<title id="title">A little way through — maze postcard</title>
<desc id="desc">{width} by {height} maze. Enter at the top left; exit at the bottom right.
Seed: {label}. {"Solution shown in rust orange." if solution else "One route connects the entrance and exit."}</desc>
<rect width="100%" height="100%" fill="#faf7ef"/>
<g fill="#243e38" font-family="Georgia, serif">
<text x="40" y="38" font-size="23">A little way through</text>
<text x="40" y="61" font-size="12">Enter above. Find your way out below.</text>
</g>
{route}
<path d="{' '.join(lines)}" fill="none" stroke="#243e38" stroke-width="2" stroke-linecap="square"/>
<text x="40" y="{page_h - 30}" fill="#52665e" font-family="monospace" font-size="11">{width} × {height} · seed {label}</text>
</svg>
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=12, help="columns, 1–100 (default: 12)")
    parser.add_argument("--height", type=int, default=16, help="rows, 1–100 (default: 16)")
    parser.add_argument("--seed", type=int, default=42, help="integer seed (default: 42)")
    parser.add_argument("--solution", action="store_true", help="draw the solution")
    parser.add_argument("--output", type=Path, help="new SVG file; otherwise write to stdout")
    args = parser.parse_args(argv)
    try:
        svg = render_svg(args.width, args.height, args.seed, args.solution)
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(svg)
        else:
            sys.stdout.write(svg)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
