#!/usr/bin/env python3
"""The Gutter: a channel that only carries downhill.

Noise Lab seed grok-1608-gutter, index 0: quiet stone and a market.
Constraint: take one number it reports and get the same number a different way.
Make a small example and a counterexample.

Heights are 5, 4, 4, 2, 2, 0. A step is a cell index. It is accepted if the
cell is on the channel and not higher than the cell just accepted. The first
step may be any cell. The drop is start minus end, and also the sum of the
descents. Those two numbers are the same report. An uphill step stays and is
marked rejected. Seed names the round; it does not change the heights.
"""

HEIGHTS = (5, 4, 4, 2, 2, 0)


def drop_ends(accepted):
    if len(accepted) < 2:
        return 0
    return HEIGHTS[accepted[0]] - HEIGHTS[accepted[-1]]


def drop_steps(accepted):
    total = 0
    for a, b in zip(accepted, accepted[1:]):
        total += HEIGHTS[a] - HEIGHTS[b]
    return total


def play(lines):
    accepted, rejected = [], []
    for line in lines:
        try:
            cell = int(str(line).strip())
        except ValueError:
            rejected.append(line)
            continue
        if cell < 0 or cell >= len(HEIGHTS):
            rejected.append(cell)
            continue
        if accepted and HEIGHTS[cell] > HEIGHTS[accepted[-1]]:
            rejected.append(cell)
            continue
        accepted.append(cell)
    return accepted, rejected


def check():
    ex = [0, 1, 2, 3, 4, 5]
    acc, rej = play(ex)
    assert acc == ex and rej == [], (acc, rej)
    assert drop_ends(acc) == drop_steps(acc) == 5
    # a level step is still downhill-or-flat; the two reports still agree
    level = [1, 2]
    acc, rej = play(level)
    assert acc == level and rej == [] and drop_ends(acc) == drop_steps(acc) == 0
    # counterexample: uphill, kept
    acc, rej = play([3, 1])
    assert acc == [3] and rej == [1]
    assert drop_ends(acc) == drop_steps(acc) == 0
    print("PASS")
    print("drop", drop_ends(ex), "two ways; uphill rejected")


if __name__ == "__main__":
    check()
