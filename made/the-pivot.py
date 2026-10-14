#!/usr/bin/env python3
"""The pivot. A joint that takes opposite pins on the open beat.

A pin is L or R. Accepted only on the open beat, and only opposite the last accepted pin.
The first may be either. Beat advances on every line. Draws when each side has taken three pins.
Off-beat, same-side, or non-pin kept and marked rejected.

Parameter: open residue 0 or 1. Default 0.

Standard library only. Nothing deleted.
"""
import sys

NEED = 3

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
        state["notes"].append(f"rejected {word!r}: not a pin")
        return state
    if not open_beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: closed beat")
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same side")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["L"] >= NEED and state["sides"]["R"] >= NEED:
        state["drawn"] = True
    return state

def check():
    s = fresh(0)
    lines = ["L", "x", "R", "y", "L", "z", "R", "a", "L", "b", "R"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 6 and s["drawn"] and s["rejected"] == 5
    print("PASS")
    print("opposite pins on open beats draw after six; rejects kept")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
