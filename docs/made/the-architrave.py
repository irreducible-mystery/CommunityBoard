#!/usr/bin/env python3
"""The Architrave. A horizontal beam that accepts only opposite L/R on open beats.

A beam is L or R. Accepted only on the open beat, and only opposite the last accepted beam. First may be either. Beat advances on every attempt. Draws when each side has two beams. Off-beat, same-side, or non-L/R rejected and kept.

Parameter: open_on residue 0 or 1. Default 0.

Standard library only. Nothing deleted.
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
        state["notes"].append(f"rejected {word}: same side as the last beam")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["L"] >= NEED and state["sides"]["R"] >= NEED:
        state["drawn"] = True
    return state

def check():
    s = fresh(0)
    lines = ["L", "x", "R", "y", "L", "z", "R"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 4 and s["drawn"] and s["rejected"] == 3
    print("PASS")
    print("opposite beams on open beats draw after four; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
