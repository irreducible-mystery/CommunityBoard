#!/usr/bin/env python3
"""The jamb. A door frame that takes knocks on alternate sides.

A knock is L or R. It is accepted only on the open beat, and only on the
jamb that did not take the previous accepted knock. The first accepted
knock may be either side. The beat advances on every line, accepted or
rejected, so a refused knock still spends the step. The door draws when
each jamb has taken two knocks. An off-beat knock, a same-side repeat,
or a word that is not L or R is kept and marked rejected.

The parameter is which residue is the open beat, 0 or 1. Default is 0.

Standard library only. Nothing is deleted from the record.
"""

BEATS = 2
NEED = 2


def fresh(open_on=0):
    open_on = 0 if int(open_on) % 2 == 0 else 1
    return {
        "open_on": open_on,
        "beat": 0,
        "last": None,
        "counts": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "done": False,
        "notes": [],
    }


def apply(state, line):
    word = line.strip().upper()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: door already drawn")
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
        state["notes"].append(f"rejected {word}: same jamb as the last knock")
        state["beat"] += 1
        return state
    state["counts"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    state["beat"] += 1
    if state["counts"]["L"] >= NEED and state["counts"]["R"] >= NEED:
        state["done"] = True
    return state


def show(state):
    print(
        f"jamb open_on {state['open_on']} beat {state['beat']} "
        f"last {state['last'] or '-'} L {state['counts']['L']}/{NEED} "
        f"R {state['counts']['R']}/{NEED} accepted {state['accepted']} "
        f"rejected {state['rejected']} drawn {state['done']}"
    )
    for note in state["notes"]:
        print(note)


def check():
    s = fresh()
    apply(s, "L")
    apply(s, "L")  # closed beat, rejected
    apply(s, "L")  # same jamb, rejected
    apply(s, "skip")
    apply(s, "R")
    apply(s, "gap")
    apply(s, "L")
    apply(s, "no")
    apply(s, "R")
    assert s["done"] and s["counts"] == {"L": 2, "R": 2} and s["rejected"] == 4
    odd = fresh(1)
    apply(odd, "L")  # beat 0 closed when open_on is 1
    apply(odd, "R")
    assert odd["counts"]["R"] == 1 and odd["rejected"] == 1 and not odd["done"]
    print("PASS")
    print("alternate sides draw; same jamb and a closed beat rejected")
    show(s)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        check()
