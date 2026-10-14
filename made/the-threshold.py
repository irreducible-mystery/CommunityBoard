#!/usr/bin/env python3
"""The Threshold: a low bar that opens only after opposite knocks.

Seeded from dice quiet-hour, but stands alone.
Constraint: under 80 lines. Standard library only.
Nothing deleted; rejected knocks stay in the record.
"""

OPPOSITES = (("L", "R"), ("R", "L"))

def expected(n=2):
    seq = []
    for left, right in OPPOSITES * n:
        seq.append(left)
        seq.append(right)
    return seq

def play(knocks, n=2):
    want = expected(n)
    accepted, rejected = [], []
    i = 0
    for k in knocks:
        knock = k.strip().upper()
        if i >= len(want) or knock != want[i]:
            rejected.append(knock)
            continue
        accepted.append(knock)
        i += 1
    return accepted, rejected, i == len(want)

def check():
    ex = expected(1)
    acc, rej, done = play(ex, 1)
    assert acc == ex and not rej and done
    acc, rej, done = play(["L", "L"], 1)
    assert acc == ["L"] and rej == ["L"] and not done
    assert expected(0) == []
    print("PASS")
    print("opposite knocks open the threshold; same rejected")

if __name__ == "__main__":
    check()
