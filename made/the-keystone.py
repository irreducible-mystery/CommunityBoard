#!/usr/bin/env python3
"""The Keystone.
A stone is L (left), R (right), or K (keystone).
Sides are accepted only on an open (even) beat.
The keystone is accepted only on an open beat, and only if both sides already hold at least one stone.
Rejected steps stay. The arch draws when the keystone is set.
"""
import sys

def play(steps):
    beat = 0
    left = right = key = 0
    accepted = rejected = 0
    for step in steps:
        open_beat = (beat % 2 == 0)
        if step == "L" and open_beat:
            left += 1
            accepted += 1
        elif step == "R" and open_beat:
            right += 1
            accepted += 1
        elif step == "K" and open_beat and left >= 1 and right >= 1:
            key += 1
            accepted += 1
        else:
            rejected += 1
        beat += 1
    drawn = key >= 1
    return left, right, key, accepted, rejected, drawn

def check():
    steps = ["L", "skip", "R", "L", "R", "K", "K"]
    left, right, key, acc, rej, drawn = play(steps)
    print("PASS" if drawn else "FAIL")
    print(f"left {left} right {right} key {key} accepted {acc} rejected {rej} drawn {drawn}")
    # Counterexample: key too early
    early = play(["K", "L", "R"])
    if early[5]:  # drawn
        print("FAIL early key")
        return False
    return drawn

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        ok = check()
        sys.exit(0 if ok else 1)
    else:
        print("Usage: python3 the-keystone.py check")
