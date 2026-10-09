#!/usr/bin/env python3
"""The Pane. Five panes, fog 0 to 3. A seed plus move lines.

breathe N adds one fog to pane N if it is not already full.
wipe N takes one fog off pane N if any is there.
wait changes nothing but the turn count.
A line that breaks a rule stays and is marked rejected.
The field is unchanged by it.

The round is clear when every pane is 0 after at least one accepted wipe.
It is spent at 12 accepted moves if fog remains. Spending the turns is
not a failure of the record.

Seed names the round and which pane starts fogged (fog 2). The others start clear.
Standard library only.
"""
from __future__ import annotations
import argparse, hashlib, sys

PANES = 5
CAP = 3
TURNS = 12

def start_index(seed: str) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return digest[0] % PANES

def fresh(seed: str):
    fog = [0] * PANES
    fog[start_index(seed)] = 2
    return {"seed": seed, "fog": fog, "turn": 0, "accepted": 0, "rejected": 0,
            "wipes": 0, "done": False, "clear": False, "notes": []}

def apply(state, line):
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: pane already spent")
        return state
    word = line.strip().split()
    if not word or word[0] not in {"breathe", "wipe", "wait"} or (word[0] != "wait" and len(word) != 2) or (word[0] == "wait" and len(word) != 1):
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    move = word[0]
    if move == "wait":
        state["turn"] += 1
        state["accepted"] += 1
    else:
        try:
            n = int(word[1])
        except ValueError:
            state["rejected"] += 1
            state["notes"].append(f"rejected {line!r}: pane not an integer")
            return state
        if n < 0 or n >= PANES:
            state["rejected"] += 1
            state["notes"].append(f"rejected {line!r}: pane out of range")
            return state
        if move == "breathe":
            if state["fog"][n] >= CAP:
                state["rejected"] += 1
                state["notes"].append(f"rejected breathe {n}: already full")
                return state
            state["fog"][n] += 1
        else:
            if state["fog"][n] <= 0:
                state["rejected"] += 1
                state["notes"].append(f"rejected wipe {n}: already clear")
                return state
            state["fog"][n] -= 1
            state["wipes"] += 1
        state["turn"] += 1
        state["accepted"] += 1
    if state["wipes"] and all(v == 0 for v in state["fog"]):
        state["done"] = True
        state["clear"] = True
    elif state["accepted"] >= TURNS:
        state["done"] = True
    return state

def show(state):
    print(f"the-pane {state['seed']}")
    print("fog " + " ".join(str(v) for v in state["fog"]))
    print(f"accepted {state['accepted']} rejected {state['rejected']} wipes {state['wipes']} clear {state['clear']} spent {state['done']}")
    for note in state["notes"]:
        print(note)

def replay(seed, lines):
    state = fresh(seed)
    for line in lines:
        if line.strip():
            apply(state, line)
    return state

def check():
    fails = []
    s = fresh("check-seed")
    idx = start_index("check-seed")
    if s["fog"][idx] != 2 or sum(s["fog"]) != 2:
        fails.append("fresh")
    before = s["fog"][:]
    apply(s, "wipe 9")
    if s["rejected"] != 1 or s["fog"] != before:
        fails.append("out of range keeps field")
    apply(s, "wipe " + str((idx + 1) % PANES))
    if s["rejected"] != 2 or s["fog"] != before:
        fails.append("wipe clear keeps field")
    apply(s, "wipe " + str(idx))
    if s["fog"][idx] != 1 or s["wipes"] != 1:
        fails.append("wipe takes one")
    apply(s, "breathe " + str(idx))
    if s["fog"][idx] != 2:
        fails.append("breathe returns fog")
    full = fresh("full")
    n = start_index("full")
    apply(full, f"breathe {n}")
    apply(full, f"breathe {n}")
    if full["rejected"] != 1 or full["fog"][n] != CAP:
        fails.append("full rejects")
    clear = fresh("clear-me")
    n = start_index("clear-me")
    apply(clear, f"wipe {n}")
    apply(clear, f"wipe {n}")
    if not clear["clear"] or not clear["done"] or sum(clear["fog"]) != 0:
        fails.append("two wipes clear the seed pane")
    if fails:
        print("FAIL " + ", ".join(fails))
        return 1
    print("PASS")
    print(f"seed pane starts at fog 2; index for check-seed is {idx}")
    return 0

def main(argv):
    p = argparse.ArgumentParser(description="The Pane. Five panes of fog, played by lines.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sh = sub.add_parser("show")
    sh.add_argument("seed")
    rp = sub.add_parser("replay")
    rp.add_argument("seed")
    rp.add_argument("path")
    args = p.parse_args(argv)
    if args.cmd == "check":
        return check()
    if args.cmd == "show":
        show(fresh(args.seed))
        return 0
    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    show(replay(args.seed, text.splitlines()))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
