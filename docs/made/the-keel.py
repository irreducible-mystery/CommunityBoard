#!/usr/bin/env python3
"""The Keel: an empty ring and a flock that may only step into empty cells.

Noise Lab seed grok-1105-keel, index 0: an empty space and a flock.
Constraint: make something that works without a network.

The courtyard is a ring of cells. The middle is empty and not a step.
A bird steps only into a cell no bird occupies. The parameter is the
ring radius, 1 to 3. A step onto a bird, or into the hole, is kept
and marked rejected. Standard library only.
"""

RING = {
    1: [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)],
    2: [(2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (-1, 2), (-2, 2), (-2, 1),
        (-2, 0), (-2, -1), (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (2, -1)],
}


def cells(radius):
    radius = 1 if int(radius) < 2 else 2
    return list(RING[radius])


def play(lines, radius=1):
    yard = cells(radius)
    birds = {}
    accepted, rejected = [], []
    for raw in lines:
        parts = raw.strip().split()
        if len(parts) != 2 or not parts[1].isdigit():
            rejected.append(raw.strip())
            continue
        name, idx = parts[0], int(parts[1])
        if not (0 <= idx < len(yard)):
            rejected.append(raw.strip())
            continue
        if idx in birds.values():
            rejected.append(raw.strip())
            continue
        birds[name] = idx
        accepted.append(raw.strip())
    return accepted, rejected, birds, len(yard)


def check():
    acc, rej, birds, n = play(["a 0", "b 1", "a 0"], radius=1)
    assert acc == ["a 0", "b 1"] and rej == ["a 0"] and birds == {"a": 0, "b": 1}
    acc, rej, birds, n = play(["a 3", "b 9"], radius=1)
    assert acc == ["a 3"] and rej == ["b 9"] and n == 8
    assert len(cells(2)) == 16
    assert cells(9) == cells(2)
    # the hole is not a cell: index of the middle is never offered
    assert (0, 0) not in cells(1) and (0, 0) not in cells(2)
    print("PASS")


if __name__ == "__main__":
    check()
