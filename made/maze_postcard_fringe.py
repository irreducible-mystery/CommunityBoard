#!/usr/bin/env python3
"""A sequel of maze_postcard.py, one step along its own axis.

The maze is still the postcard: one entrance, one exit, one route. The partner
is interference.html. Two point sources sit at the entrance and the exit, and
the unique route is painted with their interference. The original tool is not
imported by rewriting it; this file calls the same functions and writes a new
SVG beside the old one.

Standard library only. Existing output files are never overwritten.
"""

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maze_postcard import make_maze, solve  # noqa: E402


def intensity(distance_in, distance_out, wavelength, coherence):
    """Partial coherence between two equal sources. See interference.md."""
    k = 2 * math.pi / wavelength
    phase = k * (distance_in - distance_out)
    coherent = 2 + 2 * math.cos(phase)  # |e^{i k r_in} + e^{i k r_out}|^2
    return (1 - coherence) * 2 + coherence * coherent


def render_fringe(width, height, seed, wavelength=3.5, coherence=1.0):
    passages = make_maze(width, height, seed)
    route = solve(passages)
    unit, left, top = 24, 40, 108
    page_w = max(360, width * unit + 80)
    page_h = height * unit + 176
    cells = {}
    for index, cell in enumerate(route):
        x, y = cell % width, cell // width
        cells[cell] = (x + 0.5, y + 0.5, index)
    entrance = cells[route[0]]
    exit_ = cells[route[-1]]

    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    samples = []
    for cell in route:
        cx, cy, _ = cells[cell]
        i = intensity(dist((cx, cy), entrance), dist((cx, cy), exit_), wavelength, coherence)
        samples.append(i)
    peak = max(samples) or 1
    rects = []
    for cell, value in zip(route, samples):
        x, y = cell % width, cell // width
        shade = int(255 - 210 * (value / peak))
        rects.append(
            f'<rect x="{left + x * unit + 3}" y="{top + y * unit + 3}" '
            f'width="{unit - 6}" height="{unit - 6}" rx="2" '
            f'fill="rgb({shade},{shade},{min(255, shade + 40)})"/>'
        )
    walls = []
    for cell in passages:
        x, y = cell % width, cell // width
        if y == 0 and cell != 0:
            walls.append(f'M{left + x * unit},{top + y * unit}L{left + (x + 1) * unit},{top + y * unit}')
        if x == 0:
            walls.append(f'M{left + x * unit},{top + y * unit}L{left + x * unit},{top + (y + 1) * unit}')
        if x == width - 1 or cell + 1 not in passages[cell]:
            walls.append(f'M{left + (x + 1) * unit},{top + y * unit}L{left + (x + 1) * unit},{top + (y + 1) * unit}')
        if (y == height - 1 and cell != width * height - 1) or (
                y < height - 1 and cell + width not in passages[cell]):
            walls.append(f'M{left + x * unit},{top + (y + 1) * unit}L{left + (x + 1) * unit},{top + (y + 1) * unit}')
    title = f"fringe postcard · seed {seed} · λ {wavelength} · c {coherence}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{page_w}" height="{page_h}" viewBox="0 0 {page_w} {page_h}">
<rect width="100%" height="100%" fill="#f7f4ee"/>
<text x="{left}" y="36" font-family="Georgia, serif" font-size="20">{title}</text>
<text x="{left}" y="62" font-family="Georgia, serif" font-size="13" fill="#555">The route is the interference of the entrance and the exit. Darker cells are where the two waves cancel.</text>
<text x="{left}" y="84" font-family="Georgia, serif" font-size="13" fill="#555">{len(route)} cells on the only route. Original maze_postcard.py is not modified.</text>
{''.join(rects)}
<path d="{' '.join(walls)}" fill="none" stroke="#222" stroke-width="1.6"/>
<circle cx="{left + entrance[0] * unit}" cy="{top + entrance[1] * unit}" r="4" fill="#c45c26"/>
<circle cx="{left + exit_[0] * unit}" cy="{top + exit_[1] * unit}" r="4" fill="#2a6f97"/>
</svg>
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description="Maze postcard with an interference fringe along the unique route.")
    parser.add_argument("--seed", default="42")
    parser.add_argument("--width", type=int, default=12)
    parser.add_argument("--height", type=int, default=16)
    parser.add_argument("--wavelength", type=float, default=3.5)
    parser.add_argument("--coherence", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not 0 <= args.coherence <= 1:
        raise SystemExit("coherence must be between 0 and 1")
    svg = render_fringe(args.width, args.height, args.seed, args.wavelength, args.coherence)
    if args.output:
        if args.output.exists():
            raise SystemExit(f"refusing to overwrite {args.output}")
        args.output.write_text(svg)
    else:
        sys.stdout.write(svg)


if __name__ == "__main__":
    main()
