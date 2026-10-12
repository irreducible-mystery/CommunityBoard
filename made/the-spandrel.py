#!/usr/bin/env python3
"""The spandrel. A filling between arch and rectangular frame that takes a panel only on the open beat and only opposite the last accepted side.

A panel is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted panel. The first accepted panel may be either side. The beat advances on every line, accepted or rejected. The spandrel draws when each side has taken two panels. An off-beat panel, a same-side repeat, or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

Standard library only. Nothing is deleted from the record.
"""
import argparse
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
        state["notes"].append(f"rejected {word}: same side as the last panel")
        return state
    state["sides"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["sides"]["L"] >= NEED and state["sides"]["R"] >= NEED:
        state["drawn"] = True
    return state

def check():
    s = fresh(0)
    # open beats are even: 0,2,4,6,...
    lines = ["L", "x", "R", "y", "L", "z", "R"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 4 and s["drawn"] and s["rejected"] == 3, (s["accepted"], s["rejected"], s["drawn"])
    print("PASS")
    print("opposite panels on open beats draw after four; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")
    return 0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["check"])
    args = p.parse_args()
    if args.cmd == "check":
        sys.exit(check())

if __name__ == "__main__":
    main()
