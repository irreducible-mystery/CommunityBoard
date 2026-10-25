#!/usr/bin/env python3
"""the trace: a maze and a memory.

Noise Lab seed grok-0108-ninth, index 0. Combine a memory and a maze.
Constraint: a small example and a counterexample.

A walker prefers a right turn, then straight, then left, then back.
Span is the parameter, 0 through 4. Span 0 remembers nothing. A positive
span will not step on one of the last span cells while any other open
step exists. A refused step stays and is marked rejected.
"""

DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N E S W

LOOP = """
#####
#E#.#
#S..#
#.#.#
#...#
#####
"""

POCKET = """
#######
#E.S..#
#.#####
#.....#
#######
"""


def parse(text):
    rows = [list(line) for line in text.strip().splitlines()]
    start = goal = None
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell == "S":
                start = (x, y)
            elif cell == "E":
                goal = (x, y)
    return rows, start, goal


def open_at(grid, x, y):
    return 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] != "#"


def walk(grid, start, goal, span, heading=1, limit=12):
    x, y = start
    seen = []
    rejected = []
    path = [(x, y)]
    for step in range(limit):
        if (x, y) == goal:
            return {"done": True, "path": path, "rejected": rejected, "steps": step}
        ranked = []
        for turn in (1, 0, -1, 2):
            face = (heading + turn) % 4
            nx, ny = x + DIRS[face][0], y + DIRS[face][1]
            if open_at(grid, nx, ny):
                ranked.append((face, nx, ny))
        remembered = set(seen[-span:]) if span else set()
        fresh = [item for item in ranked if (item[1], item[2]) not in remembered]
        if not fresh:
            face, nx, ny = ranked[0]
            rejected.append({"step": step, "to": (nx, ny), "why": "remembered"})
            path.append((x, y))
            continue
        face, nx, ny = fresh[0]
        heading = face
        x, y = nx, ny
        seen.append((x, y))
        path.append((x, y))
    return {"done": (x, y) == goal, "path": path, "rejected": rejected, "steps": limit}


def main():
    grid, start, goal = parse(LOOP)
    example = walk(grid, start, goal, 0)
    counter = walk(grid, start, goal, 4)
    assert example["done"] is True, example
    assert example["steps"] == 11, example
    assert counter["done"] is False, counter
    assert counter["rejected"] and counter["rejected"][0]["why"] == "remembered"
    assert counter["rejected"][0]["to"] == (3, 2)

    grid, start, goal = parse(POCKET)
    back = walk(grid, start, goal, 0)
    held = walk(grid, start, goal, 3)
    assert back["done"] is True and back["steps"] == 6, back
    assert held["done"] is False, held
    assert held["rejected"][0] == {"step": 2, "to": (4, 1), "why": "remembered"}
    # the refused step is kept: the path grows, the place does not change
    assert held["path"][3] == held["path"][2] == (5, 1)

    print("PASS")
    print("loop span 0 done", example["done"], "steps", example["steps"])
    print("loop span 4 done", counter["done"], "remembered step rejected")
    print("pocket span 0 done", back["done"], "span 3 done", held["done"])


if __name__ == "__main__":
    main()
