#!/usr/bin/env python3
"""The Quoin. A corner stone that takes courses on alternate faces.

A course is N or E. It is accepted only on the open beat, and only on the
face that did not take the previous accepted course. The first accepted
course may be either face. The beat advances on every line, accepted or
rejected, so a refused course still spends the step. The corner is set
when each face has taken two courses. An off-beat course, a same-face
repeat, or a word that is not N or E is kept and marked rejected.

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
        "counts": {"N": 0, "E": 0},
        "accepted": 0,
        "rejected": 0,
        "done": False,
        "notes": [],
    }


def apply(state, line):
    word = line.strip().upper()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word!r}: corner already set")
        state["beat"] += 1
        return state
    if word not in ("N", "E"):
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: want N or E")
        state["beat"] += 1
        return state
    if state["beat"] % BEATS != state["open_on"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat {state['beat']} is closed")
        state["beat"] += 1
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same face as the last course")
        state["beat"] += 1
        return state
    state["counts"][word] += 1
    state["last"] = word
    state["accepted"] += 1
    state["beat"] += 1
    if state["counts"]["N"] >= NEED and state["counts"]["E"] >= NEED:
        state["done"] = True
    return state


def show(state):
    print(
        f"quoin open_on {state['open_on']} beat {state['beat']} "
        f"last {state['last'] or '-'} N {state['counts']['N']}/{NEED} "
        f"E {state['counts']['E']}/{NEED} accepted {state['accepted']} "
        f"rejected {state['rejected']} set {state['done']}"
    )
    for note in state["notes"]:
        print(note)


def check():
    s = fresh()
    apply(s, "N")
    apply(s, "N")  # closed beat, rejected
    apply(s, "N")  # same face, rejected
    apply(s, "skip")
    apply(s, "E")
    apply(s, "gap")
    apply(s, "N")
    apply(s, "no")
    apply(s, "E")
    assert s["done"] and s["counts"] == {"N": 2, "E": 2} and s["rejected"] == 5
    odd = fresh(1)
    apply(odd, "N")  # beat 0 closed when open_on is 1
    apply(odd, "E")
    assert odd["counts"]["E"] == 1 and odd["rejected"] == 1 and not odd["done"]
    print("PASS")
    print("alternate faces set; same face and a closed beat rejected")
    show(s)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        check()
