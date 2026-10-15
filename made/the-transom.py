#!/usr/bin/env python3
"""The transom. A bar over a door that passes one beam at a time.

A line is L or R. The beat advances on every line, accepted or rejected, so
a refused beam still spends the step. Light passes only on an open beat, and
only on one side. A line that names both sides is too wide and is kept as
rejected. The room draws when each side has passed twice. The parameter is
which residue is open, 0 or 1. Default is 0.

Made beside the stoop (a step that counts arrivals) and the pane (a window
that fogs on the line). Neither is edited. Standard library only.
"""

BEATS = 2
NEED = 2


def fresh(open_on=0):
    open_on = 0 if int(open_on) % 2 == 0 else 1
    return {
        "open_on": open_on,
        "beat": 0,
        "passed": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "done": False,
        "notes": [],
    }


def apply(state, line):
    word = line.strip().upper()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: room already drawn")
        state["beat"] += 1
        return state
    if word not in {"L", "R"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: want L or R, not both")
        state["beat"] += 1
        return state
    if state["beat"] % BEATS != state["open_on"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']} is closed")
        state["beat"] += 1
        return state
    if state["passed"][word] >= NEED:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: that side is already full")
        state["beat"] += 1
        return state
    state["passed"][word] += 1
    state["accepted"] += 1
    state["beat"] += 1
    if state["passed"]["L"] >= NEED and state["passed"]["R"] >= NEED:
        state["done"] = True
    return state


def show(state):
    print(
        f"transom open_on {state['open_on']} beat {state['beat']} "
        f"L {state['passed']['L']}/{NEED} R {state['passed']['R']}/{NEED} "
        f"accepted {state['accepted']} rejected {state['rejected']} "
        f"drawn {state['done']}"
    )
    for note in state["notes"]:
        print(note)


def check():
    s = fresh()
    for line in ("L", "both", "R", "gap", "L", "nope", "R"):
        apply(s, line)
    assert s["done"] and s["passed"] == {"L": 2, "R": 2} and s["rejected"] == 3, s
    odd = fresh(1)
    apply(odd, "L")
    assert odd["passed"]["L"] == 0 and odd["rejected"] == 1 and odd["beat"] == 1
    apply(odd, "L")
    assert odd["passed"]["L"] == 1 and not odd["done"]
    print("PASS")
    print("even takes L and R twice; both, a closed beat, and a full side rejected")


if __name__ == "__main__":
    check()
    show(fresh())
