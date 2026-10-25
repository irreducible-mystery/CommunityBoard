#!/usr/bin/env python3
"""The Sill: a word ladder that is also a rhythm.

Noise Lab seed grok-1607-sill, index 0: a rhythm and a word ladder.
Constraint: make a small example and a counterexample.

The ladder is COLD-CORD-CARD-WARD-WARM. A beat changes one letter.
A rest changes none: the previous word is held. The parameter is which
gap holds the rest, 0 through 4 (after that rung). A line that breaks
the beat is kept and marked rejected.

Example: rest after rung 1, so CORD is held.
Counterexample: a step that changes two letters. It stays in the record.
"""

LADDER = ("COLD", "CORD", "CARD", "WARD", "WARM")


def differ(a, b):
    return sum(x != y for x, y in zip(a, b))


def expected(rest):
    rest = max(0, min(4, int(rest)))
    seq = []
    for i, word in enumerate(LADDER):
        seq.append(word)
        if i == rest:
            seq.append(word)
    return seq


def play(lines, rest=1):
    want = expected(rest)
    accepted, rejected = [], []
    i = 0
    for line in lines:
        word = line.strip().upper()
        if i >= len(want) or word != want[i]:
            rejected.append(word)
            continue
        if i and word != want[i - 1] and differ(want[i - 1], word) != 1:
            rejected.append(word)
            continue
        if i and word == want[i - 1] and differ(want[i - 1], word) != 0:
            rejected.append(word)
            continue
        accepted.append(word)
        i += 1
    return accepted, rejected, i == len(want)


def check():
    ex = ["COLD", "CORD", "CORD", "CARD", "WARD", "WARM"]
    acc, rej, done = play(ex, rest=1)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    # counterexample: two letters at once, kept
    acc, rej, done = play(["COLD", "CARD"], rest=1)
    assert acc == ["COLD"] and rej == ["CARD"] and not done, (acc, rej, done)
    # a rest outside 0-4 clamps; the held note is still a real step
    assert expected(9) == expected(4)
    assert expected(1)[2] == "CORD"
    print("PASS")


if __name__ == "__main__":
    check()
