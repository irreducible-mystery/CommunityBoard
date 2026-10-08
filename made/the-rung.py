#!/usr/bin/env python3
"""The Rung: a maze whose doors are word-ladder steps.

Noise Lab seed grok-1008-eleventh, index 0: a maze and a word ladder.
Constraint: at most 100 lines. This file stays under that.

Rooms are COLD, CORD, CARD, WORD, WARD, WARM. A door exists only where
the words differ by one letter. The parameter is which door is a wall,
0 through 4. Crossing a wall stays and is marked rejected.
"""

ROOMS = ("COLD", "CORD", "CARD", "WORD", "WARD", "WARM")
# 0 COLD-CORD, 1 CORD-CARD, 2 CORD-WORD, 3 WORD-WARD, 4 WARD-WARM
EDGES = (
    ("COLD", "CORD"),
    ("CORD", "CARD"),
    ("CORD", "WORD"),
    ("WORD", "WARD"),
    ("WARD", "WARM"),
)


def differ(a, b):
    return sum(x != y for x, y in zip(a, b))


def doors(wall):
    wall = max(0, min(4, int(wall)))
    open_doors = set()
    for i, (a, b) in enumerate(EDGES):
        if i != wall and differ(a, b) == 1:
            open_doors.add((a, b))
            open_doors.add((b, a))
    return open_doors


def play(lines, wall=1):
    open_doors = doors(wall)
    accepted, rejected = [], []
    here = None
    for line in lines:
        word = line.strip().upper()
        if word not in ROOMS:
            rejected.append(word)
            continue
        if here is None:
            if word != "COLD":
                rejected.append(word)
                continue
            accepted.append(word)
            here = word
            continue
        if (here, word) not in open_doors:
            rejected.append(word)
            continue
        accepted.append(word)
        here = word
    return accepted, rejected, here == "WARM"


def check():
    route = ["COLD", "CORD", "WORD", "WARD", "WARM"]
    acc, rej, done = play(route, wall=1)
    assert acc == route and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["COLD", "CORD", "CARD"], wall=1)
    assert acc == ["COLD", "CORD"] and rej == ["CARD"] and not done
    acc, rej, done = play(route, wall=3)
    assert acc == ["COLD", "CORD", "WORD"] and rej == ["WARD", "WARM"] and not done
    assert doors(9) == doors(4)
    print("PASS")
    print("wall 1 route", len(route), "done", done, "walled rung rejected")


if __name__ == "__main__":
    check()
