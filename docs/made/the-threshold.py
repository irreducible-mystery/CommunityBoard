#!/usr/bin/env python3
"""The Threshold: a line that takes the opposite of the last accepted step.

A step is "in" or "out". It is accepted only on an open beat, and only if it
is the opposite of the previous accepted step (or any on the first). The beat
advances on every line, so a refused step still spends it. The door draws when
three alternating pairs have been accepted (six accepted steps).

Rejected lines stay in the record.
"""

OPEN_ON = 0  # even beats open


def play(lines):
    accepted = []
    rejected = []
    last = None
    beat = 0
    for raw in lines:
        word = raw.strip().lower()
        open_beat = (beat % 2 == OPEN_ON)
        ok = open_beat and word in ("in", "out") and (last is None or word != last)
        if ok:
            accepted.append(word)
            last = word
        else:
            rejected.append(word or raw.strip())
        beat += 1
    drawn = len(accepted) >= 6
    return accepted, rejected, drawn, beat


def check():
    # alternating in/out on even beats, six of them
    lines = ["in", "x", "out", "y", "in", "z", "out", "a", "in", "b", "out"]
    acc, rej, drawn, beats = play(lines)
    assert acc == ["in", "out", "in", "out", "in", "out"], acc
    assert len(rej) == 5, rej
    assert drawn, drawn
    # same as last rejected
    acc2, rej2, _, _ = play(["in", "in"])
    assert acc2 == ["in"] and rej2 == ["in"], (acc2, rej2)
    # odd beat refused even if opposite
    acc3, rej3, _, _ = play(["in", "out"])
    assert acc3 == ["in"] and "out" in rej3, (acc3, rej3)
    print("PASS")
    print(f"example accepted {len(acc)} rejected {len(rej)} drawn {drawn}")


if __name__ == "__main__":
    check()
