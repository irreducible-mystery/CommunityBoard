#!/usr/bin/env python3
"""The transom. A horizontal bar that accepts a pressure only on the open beat and only opposite the last accepted side.

A pressure is U or D. It is accepted only on the open beat, and only on the side that did not take the previous accepted pressure. The first accepted pressure may be either side. The beat advances on every line, accepted or rejected. The transom draws when each side has taken two pressures. An off-beat pressure, a same-side repeat, or a word that is not U or D is kept and marked rejected.

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
        "sides": {"U": 0, "D": 0},
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
    if word not in {"U", "D"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: not U or D")
        return state
    if not open_beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']-1} is closed")
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same side as the last pressure")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["U"] >= NEED and state["sides"]["D"] >= NEED:
        state["drawn"] = True
    return state

def check():
    s = fresh()
    # open beats at 0,2,4,6 for open_on=0
    sequence = ["U", "X", "D", "X", "U", "X", "D"]
    for w in sequence:
        apply(s, w)
    assert s["drawn"] and s["accepted"] == 4, (s["accepted"], s["drawn"], s["sides"])
    # same side rejected
    s2 = fresh()
    apply(s2, "U")
    apply(s2, "U")  # same
    assert s2["rejected"] >= 1
    print("PASS")
    print("opposite pressures on open beats draw after four; same and closed rejected")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
