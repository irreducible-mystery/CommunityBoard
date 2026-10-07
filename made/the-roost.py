#!/usr/bin/env python3
"""The Roost: a flock that only advances a word ladder by agreeing.

Noise Lab seed grok-2305-weir, index 0: a flock and a word ladder.
Constraint: let a reader change one parameter. At most 100 lines.
Standard library only.

The ladder is COLD-CORD-CARD-WARD-WARM. The parameter is the flock,
2 through 4. A rung advances only after that many birds name it.
A different word, or a word before the flock has settled, is kept
and marked rejected. Nothing is removed from the record.
"""

LADDER = ("COLD", "CORD", "CARD", "WARD", "WARM")


def flock(n):
    return max(2, min(4, int(n)))


def play(lines, n=3):
    n = flock(n)
    rung = 0
    held = 0
    accepted, rejected = [], []
    for line in lines:
        word = line.strip().upper()
        if rung >= len(LADDER) or word != LADDER[rung]:
            rejected.append(word)
            continue
        accepted.append(word)
        held += 1
        if held == n:
            rung += 1
            held = 0
    return accepted, rejected, rung == len(LADDER), n


def expected(n=3):
    n = flock(n)
    seq = []
    for word in LADDER:
        seq.extend([word] * n)
    return seq


def check():
    ex = expected(3)
    acc, rej, done, n = play(ex, 3)
    assert acc == ex and rej == [] and done and n == 3, (acc, rej, done)
    acc, rej, done, n = play(["COLD", "CORD"], 3)
    assert acc == ["COLD"] and rej == ["CORD"] and not done
    acc, rej, done, n = play(["COLD", "COLD"], 2)
    assert acc == ["COLD", "COLD"] and rej == [] and not done
    assert flock(9) == 4 and flock(1) == 2
    assert expected(2)[0:2] == ["COLD", "COLD"]
    print("PASS")
    print("flock 3 route", len(ex), "done", done, "lone bird rejected")


if __name__ == "__main__":
    check()
