#!/usr/bin/env python3
"""The apex. A summit that accepts a peak only on the open beat and only opposite the last accepted side.

A peak is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted peak. The first accepted peak may be either side. The beat advances on every line, accepted or rejected. The apex is reached when each side has taken two peaks. An off-beat peak, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

Standard library only. Nothing is deleted from the record.
"""
import sys

NEED = 2

def fresh(open_on=0):
    return {
        "open_on": open_on % 2,
        "beat": 0,
        "last": None,
        "sides": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "notes": [],
        "reached": False,
    }

def apply(state, line):
    word = line.strip()
    open_beat = (state["beat"] % 2) == state["open_on"]
    state["beat"] += 1
    if state["reached"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: already reached")
        return state
    if word not in {"L", "R"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: not L or R")
        return state
    if not open_beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']-1} is closed")
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same side as the last peak")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["L"] >= NEED and state["sides"]["R"] >= NEED:
        state["reached"] = True
    return state

def check():
    s = fresh(0)
    lines = ["L", "x", "R", "y", "L", "z", "R"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 4 and s["reached"] and s["rejected"] == 3
    print("PASS")
    print("opposite peaks on open beats reach after four; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} reached {s['reached']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
