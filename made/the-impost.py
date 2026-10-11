#!/usr/bin/env python3
"""The Impost. A stone that accepts only on the open beat, opposite the last accepted side.
Standard library only. Draws after four accepted, two each side."""
import argparse, sys

OPEN_ON = 0  # even beats open
SIDES = ("L", "R")
NEED = 2

def fresh():
    return {
        "beat": 0,
        "last": None,
        "counts": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "done": False,
        "notes": [],
    }

def open_beat(beat):
    return (beat % 2) == OPEN_ON

def apply(state, line):
    word = line.strip()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: already drawn")
        return state
    if word not in SIDES:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: want L or R")
        state["beat"] += 1
        return state
    side = word
    if not open_beat(state["beat"]):
        state["rejected"] += 1
        state["notes"].append(f"rejected {side}: beat {state['beat']} is closed")
        state["beat"] += 1
        return state
    if state["last"] == side:
        state["rejected"] += 1
        state["notes"].append(f"rejected {side}: same side as the last accepted")
        state["beat"] += 1
        return state
    # accept
    state["counts"][side] += 1
    state["accepted"] += 1
    state["last"] = side
    state["notes"].append(f"accepted {side} on beat {state['beat']}")
    state["beat"] += 1
    if state["counts"]["L"] >= NEED and state["counts"]["R"] >= NEED:
        state["done"] = True
        state["notes"].append("drawn: two each side")
    return state

def show(state):
    print(f"impost beat {state['beat']} last {state['last']}")
    print(f"L {state['counts']['L']}/{NEED}  R {state['counts']['R']}/{NEED}  accepted {state['accepted']} rejected {state['rejected']}  drawn {state['done']}")
    for note in state["notes"]:
        print(note)

def check():
    fails = []
    s = fresh()
    # beat 0 is open; L accepted
    apply(s, "L")
    if s["accepted"] != 1 or s["counts"]["L"] != 1:
        fails.append("open first")
    # beat 1 closed; R rejected
    apply(s, "R")
    if s["rejected"] != 1:
        fails.append("closed")
    # beat 2 open, same L rejected
    apply(s, "L")
    if s["rejected"] != 2:
        fails.append("same side")
    # beat 3 open? wait 3 is odd closed. Let's step carefully.
    # After two applies, beat=2. Next is beat 2 open.
    # Reset and do proper sequence
    s = fresh()
    seq = ["L", "R", "R", "L", "R", "L"]  # expect accept L, reject closed R, reject same R, accept L, accept R, accept L -> draw
    # Actually:
    # beat0 open L accept
    # beat1 closed R reject
    # beat2 open R accept (opposite)
    # beat3 closed L reject
    # beat4 open L accept
    # beat5 closed R reject
    # etc. Better rewrite sequence.
    s = fresh()
    apply(s, "L")  # 0 open accept
    apply(s, "R")  # 1 closed reject
    apply(s, "R")  # 2 open accept opposite
    apply(s, "L")  # 3 closed reject
    apply(s, "L")  # 4 open accept opposite
    apply(s, "R")  # 5 closed reject
    apply(s, "R")  # 6 open accept opposite -> should draw at 4 accepted
    if not s["done"] or s["accepted"] != 4:
        fails.append(f"draw after four got accepted {s['accepted']} done {s['done']}")
    print("PASS" if not fails else "FAIL " + ", ".join(fails))
    print("opposite sides on open beats draw after four; same and closed rejected")
    return 0 if not fails else 1

def main(argv):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    a = sub.add_parser("replay")
    a.add_argument("path")
    args = p.parse_args(argv)
    if args.cmd == "check":
        return check()
    state = fresh()
    for line in open(args.path):
        if line.strip():
            apply(state, line.strip())
    show(state)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
