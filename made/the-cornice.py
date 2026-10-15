#!/usr/bin/env python3
"""The Cornice. A projecting top course that accepts a stone only on the open beat and only opposite the last accepted face.

A stone is N or S. It is accepted only on the open beat, and only on the face that did not take the previous accepted stone. The first accepted stone may be either face. The beat advances on every line, accepted or rejected. The cornice is complete when each face has taken two stones. An off-beat stone, a same-face repeat, or a word that is not N or S is kept and marked rejected.

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
        "faces": {"N": 0, "S": 0},
        "accepted": 0,
        "rejected": 0,
        "notes": [],
        "done": False,
    }

def apply(state, line):
    word = line.strip()
    open_beat = (state["beat"] % 2) == state["open_on"]
    state["beat"] += 1
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: already done")
        return state
    if word not in {"N", "S"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: not N or S")
        return state
    if not open_beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']-1} is closed")
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same face as the last stone")
        return state
    state["faces"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    if state["faces"]["N"] >= NEED and state["faces"]["S"] >= NEED:
        state["done"] = True
    return state

def check():
    s = fresh(0)
    lines = ["N", "x", "S", "y", "N", "z", "S"]
    for line in lines:
        apply(s, line)
    assert s["accepted"] == 4 and s["done"] and s["rejected"] == 3
    print("PASS")
    print("opposite faces on open beats complete the cornice after four; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} done {s['done']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("run with check")
