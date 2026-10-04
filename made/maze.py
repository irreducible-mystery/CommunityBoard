#!/usr/bin/env python3
"""Make a printable maze: python3 made/maze.py --seed 42 > maze.svg."""
import argparse
import random
from collections import deque


def generate(width, height, seed=None):
    """Return an undirected spanning tree of a rectangular cell grid."""
    rng = random.Random(seed)
    edges = [set() for _ in range(width * height)]
    visited = {0}
    stack = [0]
    while stack:
        cell = stack[-1]
        x, y = cell % width, cell // width
        neighbors = []
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                other = ny * width + nx
                if other not in visited:
                    neighbors.append(other)
        if not neighbors:
            stack.pop()
            continue
        other = rng.choice(neighbors)
        edges[cell].add(other)
        edges[other].add(cell)
        visited.add(other)
        stack.append(other)
    return edges


def solve(edges):
    parents = {0: None}
    queue = deque([0])
    end = len(edges) - 1
    while queue:
        cell = queue.popleft()
        if cell == end:
            break
        for other in sorted(edges[cell]):
            if other not in parents:
                parents[other] = cell
                queue.append(other)
    path = [end]
    while parents[path[-1]] is not None:
        path.append(parents[path[-1]])
    return path[::-1]


def svg(width, height, edges, solution=False):
    size, margin = 24, 24
    w, h = width * size, height * size
    lines = []
    def wall(x1, y1, x2, y2):
        lines.append(f'M{x1 + margin},{y1 + margin}H{x2 + margin}' if y1 == y2
                     else f'M{x1 + margin},{y1 + margin}V{y2 + margin}')
    # Entrance above the first cell; exit below the last.
    wall(size, 0, w, 0)
    wall(0, h, w - size, h)
    wall(0, 0, 0, h)
    wall(w, 0, w, h)
    for cell, neighbors in enumerate(edges):
        x, y = cell % width, cell // width
        if x < width - 1 and cell + 1 not in neighbors:
            wall((x + 1) * size, y * size, (x + 1) * size, (y + 1) * size)
        if y < height - 1 and cell + width not in neighbors:
            wall(x * size, (y + 1) * size, (x + 1) * size, (y + 1) * size)
    route = ''
    if solution:
        points = [(margin + size / 2, margin)]
        points += [(margin + (c % width + .5) * size,
                    margin + (c // width + .5) * size) for c in solve(edges)]
        points.append((margin + w - size / 2, margin + h))
        coords = ' '.join(f'{x},{y}' for x, y in points)
        route = f'<polyline points="{coords}" fill="none" stroke="#b45309" stroke-width="3" stroke-linejoin="round"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 2 * margin} {h + 2 * margin}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{width} by {height} maze</title>'
            '<desc id="desc">Enter at the top left and exit at the bottom right.</desc>'
            '<rect width="100%" height="100%" fill="white"/>' + route +
            f'<path d="{" ".join(lines)}" fill="none" stroke="#172033" stroke-width="2" stroke-linecap="square"/></svg>')


def dimension(value):
    number = int(value)
    if not 1 <= number <= 100:
        raise argparse.ArgumentTypeError('dimensions must be between 1 and 100')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--width', type=dimension, default=20)
    parser.add_argument('--height', type=dimension, default=14)
    parser.add_argument('--seed', type=int, help='repeat the same maze with the same seed')
    parser.add_argument('--solution', action='store_true', help='draw the route in amber')
    args = parser.parse_args()
    print(svg(args.width, args.height, generate(args.width, args.height, args.seed), args.solution))


if __name__ == '__main__':
    main()
