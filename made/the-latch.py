#!/usr/bin/env python3
"""The latch. A bar that opens and closes on opposite turns, only on the open beat.

A turn is L or R. It is accepted only on the open beat, and only if it is
the opposite of the last accepted turn (the first may be either). The beat
advances on every line, accepted or rejected. The latch draws when it has
accepted two opens and two closes (four opposite turns). An off-beat turn,
a same-direction repeat, or a non-L/R word is kept and marked rejected.

Parameter: which residue is the open beat, 0 or 1. Default 0.

Standard library only. Nothing deleted.
"""

BEATS = 2
NEED = 4  # two opens, two closes


def fresh(open_on=0):
    open_on = 0 if int(open_on) % 2 == 0 else 1
    return {
        "open_on": open_on,
        "beat": 0,
        "last": None,
        "accepted": 0,
        "rejected": 0,
        "done": False,
        "notes": [],
    }


def apply(state, line):
    word = line.strip().upper()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: latch already drawn")
        state["beat"] += 1
        return state
    if word not in ("L", "R"):
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: want L or R")
        state["beat"] += 1
        return state
    if state["beat"] % BEATS != state["open_on"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']} is closed")
        state["beat"] += 1
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same direction as last accepted")
        state["beat"] += 1
        return state
    state["last"] = word
    state["accepted"] += 1
    state["beat"] += 1
    if state["accepted"] >= NEED:
        state["done"] = True
    return state


def show(state):
    print(
        f"latch open_on {state['open_on']} beat {state['beat']} "
        f"last {state['last'] or '-'} accepted {state['accepted']}/{NEED} "
        f"rejected {state['rejected']} drawn {state['done']}"
    )
    for note in state["notes"]:
        print(note)


def check():
    s = fresh()
    for line in ("L", "same", "R", "gap", "L", "no", "R"):
        apply(s, line)
    assert s["done"] and s["accepted"] == 4 and s["rejected"] == 3, s
    odd = fresh(1)
    apply(odd, "L")  # closed
    apply(odd, "R")
    assert odd["accepted"] == 1 and odd["rejected"] == 1 and not odd["done"]
    print("PASS")
    print("opposite turns on open beats draw after four; same and closed rejected")
    show(s)


if __name__ == "__main__":
    check()
