#!/usr/bin/env python3
"""The Rivet. A seed plus move lines. Standard library only. Never writes unless asked.

A plate has two sides, L and R. A pin is accepted only on the open beat, and only into the side that did not take the previous accepted pin. The beat advances on every line. The plate draws when each side has taken two pins.
"""
import argparse
import sys

SIDES = ("L", "R")


def fresh(seed):
    return {
        "seed": seed,
        "beat": 0,
        "open_on": 0,
        "last": None,
        "counts": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "notes": [],
        "drawn": False,
    }


def apply(state, line):
    word = line.strip().split()
    if state["drawn"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: already drawn")
        state["beat"] += 1
        return state
    if not word or word[0] not in SIDES:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: name L or R")
        state["beat"] += 1
        return state
    side = word[0]
    open_beat = state["beat"] % 2 == state["open_on"]
    opposite = state["last"] is None or state["last"] != side
    if not open_beat or not opposite:
        reason = "closed beat" if not open_beat else "same side as last"
        state["rejected"] += 1
        state["notes"].append(f"rejected {side}: {reason}")
    else:
        state["counts"][side] += 1
        state["last"] = side
        state["accepted"] += 1
        if state["counts"]["L"] >= 2 and state["counts"]["R"] >= 2:
            state["drawn"] = True
    state["beat"] += 1
    return state


def show(state):
    print(f"the-rivet {state['seed']}")
    print(
        f"open_on {state['open_on']} beat {state['beat']} last {state['last']} "
        f"L {state['counts']['L']}/2 R {state['counts']['R']}/2 "
        f"accepted {state['accepted']} rejected {state['rejected']} drawn {state['drawn']}"
    )
    for note in state["notes"]:
        print(note)


def load_moves(path):
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def check():
    fails = []
    s = fresh("check")
    # Closed beat rejected
    apply(s, "L")  # beat 0 open, accepted
    apply(s, "L")  # beat 1 closed, rejected
    if s["rejected"] != 1 or s["accepted"] != 1:
        fails.append("closed beat not rejected")
    # Same side rejected on open
    apply(s, "L")  # beat 2 open, same as last, rejected
    if s["rejected"] != 2 or s["accepted"] != 1:
        fails.append("same side not rejected")
    # Opposite accepted
    apply(s, "R")  # beat 3 open? wait, let's reset properly
    # Better to build a full sequence
    s = fresh("example")
    moves = ["L", "R", "L", "R"]  # all open? wait no
    # open on 0: beats 0,2,4,6 open
    # L (0 open, no last -> accept), R(1 closed reject), L(2 open, last L same reject), R(3 closed reject)
    # Need proper
    s = fresh("draw")
    sequence = ["L", "x", "R", "x", "L", "x", "R"]
    for m in sequence:
        apply(s, m)
    if not s["drawn"] or s["accepted"] != 4 or s["rejected"] != 3:
        fails.append(f"draw failed: accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        return 1
    print("PASS")
    print("opposite pins on open beats draw after four; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['drawn']}")
    return 0


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sp = sub.add_parser("show")
    sp.add_argument("path", nargs="?", default="-")
    sp.add_argument("--seed", default="show")
    args = p.parse_args()
    if args.cmd == "check":
        return check()
    moves = load_moves(args.path)
    state = fresh(args.seed)
    for m in moves:
        apply(state, m)
    show(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
