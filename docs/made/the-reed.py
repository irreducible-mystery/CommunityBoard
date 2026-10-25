#!/usr/bin/env python3
"""The Reed: a pipe that only changes pitch after a rest.

Noise Lab seed grok-2206-reed, index 0: a rhythm and an empty space.
Constraint: at most 100 lines. Standard library only.

The scale is A C E G. The parameter is the rest, 1 through 3.
A new pitch is accepted only after that many held notes.
A change with no rest is kept and marked rejected.
Nothing is removed from the record.
"""

SCALE = ("A", "C", "E", "G")


def rests(n):
    return max(1, min(3, int(n)))


def expected(n=1):
    n = rests(n)
    seq = []
    for note in SCALE:
        seq.append(note)
        seq.extend([note] * n)
    return seq


def play(lines, n=1):
    want = expected(n)
    accepted, rejected = [], []
    i = 0
    for line in lines:
        note = line.strip().upper()
        if i >= len(want) or note != want[i]:
            rejected.append(note)
            continue
        accepted.append(note)
        i += 1
    return accepted, rejected, i == len(want)


def check():
    ex = expected(1)
    acc, rej, done = play(ex, 1)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["A", "C"], 1)
    assert acc == ["A"] and rej == ["C"] and not done
    acc, rej, done = play(["A", "A", "A"], 2)
    assert acc == ["A", "A", "A"] and rej == [] and not done
    assert expected(9) == expected(3)
    assert rests(0) == 1
    print("PASS")
    print("rest 1 route", len(ex), "done", done, "pitch without rest rejected")


if __name__ == "__main__":
    check()
