#!/usr/bin/env python3
"""The springer. The first stones that start an arch.

A stone is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted stone. The first accepted stone may be either side. The beat advances on every line, accepted or rejected. The arch starts (draws) when each side has taken one stone. An off-beat stone, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

Standard library only. Nothing is deleted from the record.
"""
import sys

NEED = 1

def fresh(open_on=0):
    return {
        "open_on": open_on % 2,
        "beat": 0,
        "last": None,
        "sides": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "notes": [],
        "drawn": False,
    }

def apply(state, line):
    word = line.strip()
    open_beat = (state["beat"] % 2) == state["open_on"]
    state["beat"] += 1
    if state["drawn"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: already drawn")
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
        state["notes"].append(f"rejected {word}: same side as the last stone")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["L"] >= NEED and state["sides"]["R"] >= NEED:
        state["drawn"] = True
    return state

def check():
    s = fresh(0)
    lines = ["L", "x", "R", "y"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 2 and s["drawn"] and s["rejected"] == 2
    print("PASS")
    print("opposite stones on open beats start the arch after two; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
