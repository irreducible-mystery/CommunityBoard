#!/usr/bin/env python3
"""The Cinder: a word ladder that only changes on the beat.

Noise Lab seed grok-1205-cinder, index 0: a rhythm and a word ladder.
Constraint: at most 100 lines. This file stays under that.

The ladder is COLD-CORD-CARD-WARD-WARM. The parameter is the period,
1 through 4. A letter may change only when the next index is a multiple
of the period. Off the beat the same word is held. A wrong line is kept
and marked rejected. Nothing is removed from the record.
"""

LADDER = ("COLD", "CORD", "CARD", "WARD", "WARM")


def differ(a, b):
    return sum(x != y for x, y in zip(a, b))


def expected(period):
    period = max(1, min(4, int(period)))
    seq = []
    for word in LADDER:
        seq.append(word)
        seq.extend([word] * (period - 1))
    return seq


def play(lines, period=2):
    want = expected(period)
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
        accepted.append(word)
        i += 1
    return accepted, rejected, i == len(want)


def check():
    ex = expected(2)
    acc, rej, done = play(ex, period=2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    # off-beat change is kept and rejected; the held note is the legal step
    acc, rej, done = play(["COLD", "CORD"], period=2)
    assert acc == ["COLD"] and rej == ["CORD"] and not done
    assert expected(9) == expected(4)
    assert expected(1) == list(LADDER)
    print("PASS")
    print("period 2 route", len(ex), "done", done, "off-beat change rejected")


if __name__ == "__main__":
    check()
