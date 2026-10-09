#!/usr/bin/env python3
"""The Quay: a dock where the boat and the tide must agree.

Noise Lab seed grok-1908-quay, index 0: a rhythm and a word ladder.
Constraint: a small example and a counterexample.

Tide starts high and turns only after an accepted boat. A skiff is
taken on high water. A barge is taken on low water. A line that
disagrees is kept and marked rejected, and the tide does not turn.

Example: SKIFF, BARGE, SKIFF, BARGE.
Counterexample: BARGE on the opening high. It stays in the record.
"""

BOATS = ("SKIFF", "BARGE")


def play(lines):
    tide = "high"
    accepted, rejected = [], []
    for line in lines:
        boat = line.strip().upper()
        ok = (boat == "SKIFF" and tide == "high") or (boat == "BARGE" and tide == "low")
        if boat not in BOATS or not ok:
            rejected.append(boat)
            continue
        accepted.append(boat)
        tide = "low" if tide == "high" else "high"
    done = accepted == ["SKIFF", "BARGE", "SKIFF", "BARGE"]
    return accepted, rejected, done, tide


def check():
    acc, rej, done, tide = play(["SKIFF", "BARGE", "SKIFF", "BARGE"])
    assert acc == ["SKIFF", "BARGE", "SKIFF", "BARGE"] and rej == [] and done and tide == "high", (acc, rej, done, tide)
    acc, rej, done, tide = play(["BARGE", "SKIFF", "BARGE"])
    assert acc == [] and rej == ["BARGE", "SKIFF", "BARGE"] and not done and tide == "high", (acc, rej, done, tide)
    acc, rej, done, tide = play(["SKIFF", "SKIFF", "BARGE"])
    assert acc == ["SKIFF", "BARGE"] and rej == ["SKIFF"] and not done and tide == "high", (acc, rej, done, tide)
    acc, rej, done, tide = play(["skiff", "barge"])
    assert acc == ["SKIFF", "BARGE"] and rej == [] and not done
    print("PASS")
    print("high takes skiff; barge on high rejected; tide unturned")


if __name__ == "__main__":
    check()
