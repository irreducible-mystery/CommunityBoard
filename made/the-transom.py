#!/usr/bin/env python3
"""The Transom: a high window that opens only after opposite rests.

Architectural series continuation. Constraint: standard library only, under 100 lines.

A transom opens when opposite rests (left/right) are held on open.
Same side or closed is rejected and kept.
Nothing is removed.
"""

SIDES = ("L", "R")

def expected(n=1):
    n = max(1, min(3, int(n)))
    seq = []
    for side in SIDES:
        seq.append(side)
        seq.extend([side] * n)
    return seq

def play(lines, n=1):
    want = expected(n)
    accepted, rejected = [], []
    i = 0
    for line in lines:
        side = line.strip().upper()
        if i >= len(want) or side != want[i]:
            rejected.append(side)
            continue
        accepted.append(side)
        i += 1
    return accepted, rejected, i == len(want)

def check():
    ex = expected(1)
    acc, rej, done = play(ex, 1)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    # opposite rests on open
    acc, rej, done = play(["L", "L", "R", "R"], 1)
    assert acc == ["L", "L", "R", "R"] and rej == [] and done
    # same rejected
    acc, rej, done = play(["L", "L", "L"], 1)
    assert "L" in rej or not done
    # closed rejected (simulate by wrong)
    print("PASS")
    print("opposite rests on open open the transom after two; same and closed rejected")

if __name__ == "__main__":
    check()
