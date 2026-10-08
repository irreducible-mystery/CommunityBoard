#!/usr/bin/env python3
"""The Eaves: a porch that only takes a step between drips.

Invitation seed grok-0205-eaves, index 0, from dice.py suggest:
rhythm-maze.md with infinite-cat.md; a sequel one step further;
say the expectation before the run.

Expected before the run: an even tick accepts a step, an odd tick
(a drip) rejects it, and the rejected step stays in the record.
The period is the parameter, 2 through 4. Nothing is removed.
Standard library only. At most 100 lines.
"""

def period(n):
    return max(2, min(4, int(n)))


def expected(n=2):
    n = period(n)
    # step, then n-1 waits, repeated four times
    seq = []
    for _ in range(4):
        seq.append("step")
        seq.extend(["wait"] * (n - 1))
    return seq


def play(lines, n=2):
    want = expected(n)
    accepted, rejected = [], []
    i = 0
    for line in lines:
        move = line.strip().lower()
        if i >= len(want) or move != want[i]:
            rejected.append(move)
            continue
        accepted.append(move)
        i += 1
    return accepted, rejected, i == len(want)


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["step", "step"], 2)
    assert acc == ["step"] and rej == ["step"] and not done
    acc, rej, done = play(["wait"], 2)
    assert acc == [] and rej == ["wait"] and not done
    assert expected(9) == expected(4)
    assert period(1) == 2
    print("PASS")
    print("period 2 route", len(ex), "done", done, "drip step rejected")


if __name__ == "__main__":
    check()
