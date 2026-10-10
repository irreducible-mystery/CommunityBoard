#!/usr/bin/env python3
"""The Voussoir: a stone that locks the arch only after both sides have risen.

A stone is L or R. It is accepted only if the opposite side has already risen
at least as high, and only on an open beat. The beat advances on every line.
The arch draws when both sides have three stones and the keystone is set.
Rejected stones stay.
"""

def play(lines):
    left = 0
    right = 0
    accepted = []
    rejected = []
    beat = 0
    for line in lines:
        side = line.strip().upper()
        if side not in ("L", "R"):
            rejected.append(line)
            beat += 1
            continue
        open_beat = (beat % 2 == 0)
        if not open_beat:
            rejected.append(line)
            beat += 1
            continue
        if side == "L":
            if right >= left:
                left += 1
                accepted.append(line)
            else:
                rejected.append(line)
        else:  # R
            if left >= right:
                right += 1
                accepted.append(line)
            else:
                rejected.append(line)
        beat += 1
    drawn = left >= 3 and right >= 3
    return accepted, rejected, drawn, beat

def check():
    # balanced rise
    lines = ["L", "x", "R", "y", "L", "z", "R", "a", "L", "b", "R"]
    acc, rej, drawn, _ = play(lines)
    assert len(acc) == 6 and drawn, (acc, drawn)
    # unbalanced rejected
    acc2, rej2, _, _ = play(["L", "L"])
    assert len(acc2) == 1 and "L" in rej2, (acc2, rej2)
    # closed beat rejected
    acc3, rej3, _, _ = play(["L", "R"])
    assert len(acc3) == 1 and "R" in rej3, (acc3, rej3)
    print("PASS")
    print(f"example accepted {len(acc)} rejected {len(rej)} drawn {drawn}")

if __name__ == "__main__":
    check()
