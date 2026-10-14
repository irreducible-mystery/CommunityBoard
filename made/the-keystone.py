#!/usr/bin/env python3
"""The Keystone: opposite voussoirs draw the arch after four on the open beat.

Noise Lab seed grok-2210-keystone, index 0: an empty space and a wedge.
Constraint: at most 100 lines. Standard library only.

A voussoir is L or R. Accepted only on open beat, opposite the last.
After one of each, the keystone I is accepted once on open beat and draws.
Same side, closed beat, early or repeated I rejected and kept.
Nothing is removed from the record.
"""

def fresh():
    return {"beat": 0, "last": None, "sides": {"L": 0, "R": 0}, "drawn": False, "accepted": [], "rejected": []}

def apply(state, stone):
    stone = stone.strip().upper()
    open_beat = state["beat"] % 2 == 0
    state["beat"] += 1
    if state["drawn"] or stone not in {"L", "R", "I"} or not open_beat:
        state["rejected"].append(stone)
        return
    if stone == "I":
        if not all(state["sides"].values()):
            state["rejected"].append(stone)
            return
        state["drawn"] = True
        state["accepted"].append(stone)
        return
    if stone == state["last"]:
        state["rejected"].append(stone)
        return
    state["sides"][stone] += 1
    state["last"] = stone
    state["accepted"].append(stone)

def check():
    s = fresh()
    for st in ["L", "R", "L", "R", "I"]:
        apply(s, st)
    assert s["drawn"] and len(s["accepted"]) == 5 and len(s["rejected"]) == 0
    s2 = fresh()
    for st in ["L", "L", "I"]:
        apply(s2, st)
    assert not s2["drawn"] and "I" in s2["rejected"]
    print("PASS")
    print("opposite voussoirs on open beats draw after four; same and closed rejected")

if __name__ == "__main__":
    check()
