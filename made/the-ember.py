#!/usr/bin/env python3
"""The Ember: a flock that only steps on the beat.

Noise Lab seed grok-1305-ember, index 0: a flock and a rhythm.
Constraint: let a reader change one parameter. The parameter is the period.

Three birds start on seats 0, 2, 4 of a ring of 6. A line is `step NAME SEAT`
or `rest`. A step is accepted only on the beat (tick modulo period is 0),
onto a free seat. A rest is accepted only off the beat. A wrong line is kept
and marked rejected. Period is clamped to 1..4. Standard library only.
"""

BIRDS = ("a", "b", "c")
SEATS = (0, 1, 2, 3, 4, 5)


def play(lines, period=2):
    period = max(1, min(4, int(period)))
    birds = {"a": 0, "b": 2, "c": 4}
    accepted, rejected = [], []
    for tick, raw in enumerate(lines):
        line = raw.strip()
        parts = line.split()
        on = tick % period == 0
        ok = False
        if parts == ["rest"] and not on:
            ok = True
        elif len(parts) == 3 and parts[0] == "step" and on and parts[2].isdigit():
            name, seat = parts[1], int(parts[2])
            if name in birds and seat in SEATS and seat not in birds.values():
                birds[name] = seat
                ok = True
        (accepted if ok else rejected).append(line)
    return accepted, rejected, birds, period


def check():
    acc, rej, birds, period = play(["step a 1", "rest", "step b 3", "rest"], period=2)
    assert acc == ["step a 1", "rest", "step b 3", "rest"] and rej == []
    assert birds == {"a": 1, "b": 3, "c": 4} and period == 2
    acc, rej, birds, _ = play(["step a 1"], period=2)
    assert acc == ["step a 1"] and rej == []
    # off-beat step is kept and rejected; the seat does not change
    acc, rej, birds, _ = play(["rest", "step a 1"], period=2)
    assert acc == [] and rej == ["rest", "step a 1"] and birds["a"] == 0
    # collision stays
    acc, rej, birds, _ = play(["step a 2"], period=1)
    assert acc == [] and rej == ["step a 2"] and birds["b"] == 2
    assert play(["step a 1"], period=9)[3] == 4
    print("PASS")
    print("period 2 route 4 done True off-beat step rejected")


if __name__ == "__main__":
    check()
