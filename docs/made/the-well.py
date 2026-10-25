#!/usr/bin/env python3
"""The Well. A seed plus move lines. Standard library only. Never writes unless asked."""
import argparse, hashlib, sys

FLOOR = 5
ROPE = 8
CAP = 3
FILLS = 3

def tide(seed, step):
    digest = hashlib.sha256(f"the-well/1|{seed}|{step}".encode()).digest()
    return digest[0] % (FLOOR + 1)

def fresh(seed):
    return {"seed": seed, "rung": 0, "water": tide(seed, 0), "rope": ROPE,
            "held": 0, "filled": 0, "units": 0, "turn": 0,
            "accepted": 0, "rejected": 0, "done": False, "notes": []}

def apply(state, line):
    word = line.strip().split()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: round already drawn")
        return state
    if len(word) != 1 or word[0] not in {"down", "up", "draw", "rest"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    move = word[0]
    if move == "down":
        if state["rung"] >= FLOOR or state["rope"] <= 0:
            state["rejected"] += 1
            state["notes"].append(f"rejected down: rung {state['rung']} rope {state['rope']}")
            return state
        state["rung"] += 1
        state["rope"] -= 1
    elif move == "up":
        if state["rung"] <= 0:
            state["rejected"] += 1
            state["notes"].append("rejected up: already at the lip")
            return state
        state["rung"] -= 1
    elif move == "draw":
        if state["rung"] != state["water"] or state["held"] >= CAP:
            state["rejected"] += 1
            state["notes"].append(f"rejected draw: bucket {state['rung']} water {state['water']} held {state['held']}")
            return state
        state["held"] += 1
        state["units"] += 1
        if state["held"] == CAP:
            state["filled"] += 1
            state["held"] = 0
        state["water"] = tide(state["seed"], state["filled"] + state["units"])
    state["turn"] += 1
    state["accepted"] += 1
    if state["filled"] >= FILLS or (state["rope"] == 0 and state["rung"] == 0 and state["held"] == 0):
        state["done"] = True
    return state

def show(state):
    print(f"the-well {state['seed']}")
    print(f"bucket rung {state['rung']}  water {state['water']}  rope {state['rope']}  held {state['held']}")
    print(f"filled {state['filled']}/{FILLS}  units {state['units']}  accepted {state['accepted']} rejected {state['rejected']}  drawn {state['done']}")
    for note in state["notes"]:
        print(note)

def check():
    fails = []
    s = fresh("check")
    if s["water"] != tide("check", 0):
        fails.append("fresh water")
    apply(s, "down")
    if s["rung"] != 1 or s["rope"] != ROPE - 1:
        fails.append("down")
    apply(s, "nope")
    if s["rejected"] != 1 or s["rung"] != 1:
        fails.append("reject keeps field")
    w = fresh("draw-me")
    # walk to water and draw once
    guard = 0
    while w["rung"] != w["water"] and guard < 10:
        apply(w, "down" if w["rung"] < w["water"] else "up")
        guard += 1
    before = w["units"]
    apply(w, "draw")
    if w["units"] != before + 1:
        fails.append("draw on water")
    dry = fresh("dry")
    if dry["rung"] == dry["water"]:
        apply(dry, "down")
    apply(dry, "draw")
    if dry["rejected"] < 1:
        fails.append("draw off water")
    lip = fresh("lip")
    apply(lip, "up")
    if lip["rejected"] != 1:
        fails.append("up at lip")
    # rope does not refund
    rope = fresh("rope")
    apply(rope, "down")
    apply(rope, "up")
    if rope["rope"] != ROPE - 1:
        fails.append("rope remembers")
    print("PASS" if not fails else "FAIL " + ", ".join(fails))
    return 0 if not fails else 1

def main(argv):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    a = sub.add_parser("show"); a.add_argument("seed")
    b = sub.add_parser("replay"); b.add_argument("seed"); b.add_argument("path")
    args = p.parse_args(argv)
    if args.cmd == "check":
        return check()
    state = fresh(args.seed)
    if args.cmd == "replay":
        for line in open(args.path):
            if line.strip():
                apply(state, line.strip())
    show(state)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
