#!/usr/bin/env python3
"""The eave. An overhang that accepts a drip only on the open beat and only opposite the last accepted side.

A drip is L or R. Accepted only on the open beat, only opposite the last accepted drip. First may be either. Beat advances on every line. Draws when each side has two. Off-beat, same-side, or non L/R kept and rejected.

Standard library only. Nothing deleted.
"""
import sys

NEED = 2

def fresh(open_on=0):
    return {"open_on": open_on % 2, "beat": 0, "last": None, "sides": {"L": 0, "R": 0}, "accepted": 0, "rejected": 0, "drawn": False}

def apply(state, line):
    word = line.strip()
    open_beat = (state["beat"] % 2) == state["open_on"]
    state["beat"] += 1
    if state["drawn"] or word not in {"L", "R"} or not open_beat or state["last"] == word:
        state["rejected"] += 1
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["L"] >= NEED and state["sides"]["R"] >= NEED:
        state["drawn"] = True
    return state

def check():
    s = fresh(0)
    for line in ["L", "x", "R", "y", "L", "z", "R"]:
        apply(s, line)
    assert s["accepted"] == 4 and s["drawn"] and s["rejected"] == 3
    print("PASS")
    print("opposite drips on open beats draw after four; same and closed rejected")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
