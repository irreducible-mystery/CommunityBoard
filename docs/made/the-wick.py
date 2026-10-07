#!/usr/bin/env python3
"""The Wick. A seed plus move lines. Standard library only. Never writes unless asked."""
import argparse, sys

WAX = 4
CAP = 7
GLOWS = 5

def fresh(seed):
    return {"seed": seed, "wax": WAX, "lit": False, "glows": 0, "turn": 0,
            "accepted": 0, "rejected": 0, "done": False, "notes": []}

def apply(state, line):
    word = line.strip().split()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: wick already spent")
        return state
    if len(word) != 1 or word[0] not in {"dip", "trim", "light", "snuff", "hold"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    move = word[0]
    if move == "dip":
        if state["lit"] or state["wax"] >= CAP:
            state["rejected"] += 1
            state["notes"].append(f"rejected dip: lit {state['lit']} wax {state['wax']}")
            return state
        state["wax"] += 1
    elif move == "trim":
        if state["lit"] or state["wax"] <= 1:
            state["rejected"] += 1
            state["notes"].append(f"rejected trim: lit {state['lit']} wax {state['wax']}")
            return state
        state["wax"] -= 1
    elif move == "light":
        if state["lit"] or state["wax"] < 2:
            state["rejected"] += 1
            state["notes"].append(f"rejected light: lit {state['lit']} wax {state['wax']}")
            return state
        state["lit"] = True
        state["wax"] -= 1
        state["glows"] += 1
    elif move == "snuff":
        if not state["lit"]:
            state["rejected"] += 1
            state["notes"].append("rejected snuff: already dark")
            return state
        state["lit"] = False
    else:  # hold
        if state["lit"]:
            state["wax"] -= 1
            state["glows"] += 1
    state["turn"] += 1
    state["accepted"] += 1
    if state["wax"] <= 0 or state["glows"] >= GLOWS:
        state["wax"] = max(state["wax"], 0)
        state["lit"] = False
        state["done"] = True
    return state

def show(state):
    print(f"the-wick {state['seed']}")
    print(f"wax {state['wax']}  lit {state['lit']}  glows {state['glows']}/{GLOWS}")
    print(f"accepted {state['accepted']} rejected {state['rejected']}  spent {state['done']}")
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
    s = fresh("check")
    if s["wax"] != WAX or s["lit"]:
        fails.append("fresh")
    apply(s, "nope")
    if s["rejected"] != 1 or s["wax"] != WAX:
        fails.append("reject keeps field")
    apply(s, "light")
    if not s["lit"] or s["wax"] != WAX - 1 or s["glows"] != 1:
        fails.append("light burns one")
    apply(s, "dip")
    if s["rejected"] != 2 or s["wax"] != WAX - 1:
        fails.append("dip while lit")
    apply(s, "hold")
    if s["glows"] != 2 or s["wax"] != WAX - 2:
        fails.append("hold burns")
    apply(s, "snuff")
    if s["lit"]:
        fails.append("snuff")
    dark = fresh("dark")
    apply(dark, "snuff")
    if dark["rejected"] != 1:
        fails.append("snuff dark")
    spent = fresh("spent")
    apply(spent, "light")
    apply(spent, "hold")
    apply(spent, "hold")
    apply(spent, "hold")
    if not spent["done"] or spent["wax"] != 0 or spent["glows"] != 4:
        fails.append("spent at zero")
    after = fresh("after")
    apply(after, "light"); apply(after, "hold"); apply(after, "hold"); apply(after, "hold")
    apply(after, "hold")
    if after["rejected"] != 1 or after["accepted"] != 4:
        fails.append("move after spent kept")
    if fails:
        print("FAIL " + ", ".join(fails))
        return 1
    print("PASS")
    return 0

def main(argv):
    p = argparse.ArgumentParser(description="The Wick. A candle of seven, played by lines.")
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
