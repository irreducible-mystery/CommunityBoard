#!/usr/bin/env python3
"""The keystone. The last stone of an arch, accepted only on the open beat and only after opposite voussoirs are set.

A stone is L, R, or K. L and R are accepted only on the open beat and only opposite the last accepted side. The first may be either. K (the keystone) is accepted only on the open beat, only after each side has one, and only once. The arch draws when the keystone is set. The beat advances on every line. Same-side, off-beat, early keystone, or other words are kept and marked rejected.

Parameter: open beat residue, 0 or 1. Default 0.

Standard library only. Nothing is deleted from the record.
"""
import sys

def fresh(open_on=0):
    return {
        "open_on": open_on % 2,
        "beat": 0,
        "last": None,
        "sides": {"L": 0, "R": 0},
        "key": False,
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
    if word not in {"L", "R", "K"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: not L, R or K")
        return state
    if not open_beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']-1} is closed")
        return state
    if word == "K":
        if state["sides"]["L"] < 1 or state["sides"]["R"] < 1 or state["key"]:
            state["rejected"] += 1
            state["notes"].append(f"rejected K: supports incomplete or already set")
            return state
        state["key"] = True
        state["accepted"] += 1
        state["drawn"] = True
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same side as the last stone")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    return state

def check():
    s = fresh(0)
    lines = ["L", "x", "R", "y", "K"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 3 and s["drawn"] and s["rejected"] == 2 and s["key"]
    # early K rejected
    s2 = fresh(0)
    apply(s2, "L")
    apply(s2, "K")
    assert s2["rejected"] == 1 and not s2["key"]
    print("PASS")
    print("opposite stones then keystone on open beats draw; same, closed, early K rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
