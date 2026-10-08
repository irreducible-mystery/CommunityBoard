#!/usr/bin/env python3
"""The Stave: a word ladder scored in bars.

Noise Lab seed grok-0305-ford, index 0: a word ladder and a rhythm.
Constraint: a small example and a counterexample.

The ladder is COLD-CORD-CARD-WARD-WARM. The parameter is the meter,
2 through 4. A letter may change only on the first beat of a bar.
The other beats hold the word. A wrong line is kept and marked rejected.
Nothing is removed from the record.
"""

LADDER = ("COLD", "CORD", "CARD", "WARD", "WARM")


def differ(a, b):
    return sum(x != y for x, y in zip(a, b))


def expected(meter):
    meter = max(2, min(4, int(meter)))
    seq = []
    for word in LADDER:
        seq.append(word)
        seq.extend([word] * (meter - 1))
    return seq


def play(lines, meter=3):
    want = expected(meter)
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
    ex = expected(3)
    acc, rej, done = play(ex, meter=3)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    # counterexample: a change on the second beat is kept and rejected
    acc, rej, done = play(["COLD", "CORD"], meter=3)
    assert acc == ["COLD"] and rej == ["CORD"] and not done
    # a two-letter jump is not a rung
    acc, rej, done = play(["COLD", "COLD", "COLD", "WARM"], meter=3)
    assert acc == ["COLD", "COLD", "COLD"] and rej == ["WARM"] and not done
    assert expected(1) == expected(2)
    assert expected(9) == expected(4)
    print("PASS")
    print("meter 3 route", len(ex), "done", done, "off-beat change rejected")


if __name__ == "__main__":
    check()
