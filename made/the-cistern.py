#!/usr/bin/env python3
"""The Cistern: a word ladder that only changes a letter on the beat.

Noise Lab seed grok-1808-cistern, index 0: a word ladder and a rhythm.
Constraint: make a small example and a counterexample.

The ladder is COLD, CORD, CARD, WARD, WARM. A step is a word. It is accepted
if it is on the ladder and differs from the last accepted word by exactly one
letter, and only when the tick is on the beat (tick % period == 0). A hold,
the same word again, is accepted off the beat. An off-beat change, a two-letter
jump, or a word off the ladder stays and is marked rejected. Period is 2.
Seed names the round; it does not change the ladder.
"""

LADDER = ("COLD", "CORD", "CARD", "WARD", "WARM")
PERIOD = 2


def one_letter(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def play(lines, period=PERIOD):
    accepted, rejected = [], []
    tick = 0
    for line in lines:
        word = str(line).strip().upper()
        on_beat = tick % period == 0
        last = accepted[-1] if accepted else None
        ok = word in LADDER
        if ok and last is None:
            ok = on_beat
        elif ok and word == last:
            ok = not on_beat
        elif ok:
            ok = on_beat and one_letter(last, word)
        if ok:
            accepted.append(word)
            tick += 1
        else:
            rejected.append(word)
    done = accepted == [
        "COLD", "COLD", "CORD", "CORD", "CARD", "CARD", "WARD", "WARD", "WARM"
    ]
    return {"accepted": accepted, "rejected": rejected, "done": done, "tick": tick}


def main():
    example = ["COLD", "COLD", "CORD", "CORD", "CARD", "CARD", "WARD", "WARD", "WARM"]
    good = play(example)
    assert good["done"], good
    assert good["rejected"] == []
    early = play(["COLD", "CORD"])
    assert early["accepted"] == ["COLD"]
    assert early["rejected"] == ["CORD"]
    assert early["done"] is False
    jump = play(["COLD", "COLD", "CARD"])
    assert jump["accepted"] == ["COLD", "COLD"]
    assert jump["rejected"] == ["CARD"]
    off = play(["WARD"])
    assert off["accepted"] == []
    assert off["rejected"] == ["WARD"]
    print("PASS")
    print(
        "period", PERIOD,
        "route", len(good["accepted"]),
        "done", early["done"],
        "off-beat change rejected",
    )


if __name__ == "__main__":
    main()
