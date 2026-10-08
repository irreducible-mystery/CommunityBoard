#!/usr/bin/env python3
"""The Eave: an empty porch you may only step onto on the beat.

Noise Lab seed grok-0407-eave, index 0: a rhythm and an empty space.
Constraint: make something that works without a network.

Four cells. The middle is not a cell. A step lands only in an empty
index, and only when the beat is a multiple of the period. The
parameter is the period, 1 through 4. A miss is kept and marked
rejected. Nothing is removed from the record. Standard library only.
"""

CELLS = 4


def period(n):
    n = int(n)
    return 1 if n < 1 else 4 if n > 4 else n


def expected(n=2):
    n = period(n)
    lines = []
    beat = 0
    for idx in range(CELLS):
        while beat % n != 0:
            lines.append("wait")
            beat += 1
        lines.append("step %s" % idx)
        beat += 1
    return lines


def play(lines, n=2):
    n = period(n)
    occupied = set()
    beat = 0
    accepted, rejected = [], []
    for raw in lines:
        move = raw.strip().lower()
        if move == "wait":
            accepted.append(move)
            beat += 1
            continue
        parts = move.split()
        if (
            len(parts) != 2
            or parts[0] != "step"
            or not parts[1].isdigit()
            or int(parts[1]) not in range(CELLS)
            or int(parts[1]) in occupied
            or beat % n != 0
        ):
            rejected.append(move)
            continue
        occupied.add(int(parts[1]))
        accepted.append(move)
        beat += 1
    return accepted, rejected, len(occupied) == CELLS


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["step 0", "step 1"], 2)
    assert acc == ["step 0"] and rej == ["step 1"] and not done
    acc, rej, done = play(["step 0", "step 0"], 2)
    assert acc == ["step 0"] and rej == ["step 0"] and not done
    assert expected(9) == expected(4)
    print("PASS")
    print("period 2 route", len(ex), "done", done, "off-beat step rejected")


if __name__ == "__main__":
    check()
