#!/usr/bin/env python3
"""The stoop. A step that counts arrivals and opens on the third even beat.

A visitor may stand only when the beat is even. The beat advances on every
line, accepted or rejected, so a refused arrival still spends the step.
The door draws when three visitors have been accepted. An odd-beat arrival
is kept and marked rejected. The parameter is which residue is the open
beat, 0 or 1. Default is 0 (even).

Standard library only. Nothing is deleted from the record.
"""

BEATS = 2
NEED = 3


def fresh(open_on=0):
    open_on = 0 if int(open_on) % 2 == 0 else 1
    return {
        "open_on": open_on,
        "beat": 0,
        "stood": [],
        "accepted": 0,
        "rejected": 0,
        "done": False,
        "notes": [],
    }


def apply(state, line):
    word = line.strip()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: door already drawn")
        state["beat"] += 1
        return state
    if not word or " " in word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: want one name")
        state["beat"] += 1
        return state
    if state["beat"] % BEATS != state["open_on"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']} is closed")
        state["beat"] += 1
        return state
    if word in state["stood"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: already on the stoop")
        state["beat"] += 1
        return state
    state["stood"].append(word)
    state["accepted"] += 1
    state["beat"] += 1
    if state["accepted"] >= NEED:
        state["done"] = True
    return state


def show(state):
    print(
        f"stoop open_on {state['open_on']} beat {state['beat']} "
        f"stood {','.join(state['stood']) or '-'} "
        f"accepted {state['accepted']}/{NEED} rejected {state['rejected']} "
        f"drawn {state['done']}"
    )
    for note in state["notes"]:
        print(note)


def check():
    s = fresh()
    apply(s, "ada")
    apply(s, "skip")  # odd, rejected, beat still advances
    apply(s, "bea")
    apply(s, "gap")
    apply(s, "cy")
    assert s["done"] and s["stood"] == ["ada", "bea", "cy"] and s["rejected"] == 2
    odd = fresh(1)
    apply(odd, "nope")
    apply(odd, "ada")
    assert odd["stood"] == ["ada"] and odd["rejected"] == 1
    again = fresh()
    apply(again, "ada")
    apply(again, "skip")
    apply(again, "ada")
    assert again["rejected"] == 2 and again["stood"] == ["ada"]
    print("PASS")
    print("even takes three; odd beat and a repeat rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(check())
