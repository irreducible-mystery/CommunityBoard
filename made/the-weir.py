#!/usr/bin/env python3
"""The Weir. Two wicks, one flame that passes only when both have wax.
Standard library only. Never writes unless asked."""
import argparse, sys

WAX = 4
CAP = 7

def fresh(seed):
    return {"seed": seed, "a": WAX, "b": WAX, "lit": None, "passes": 0,
            "turn": 0, "accepted": 0, "rejected": 0, "done": False, "notes": []}

def apply(state, line):
    word = line.strip().split()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: weir already spent")
        return state
    if len(word) != 1 or word[0] not in {"light-a", "light-b", "pass", "snuff", "hold"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    move = word[0]
    if move in {"light-a", "light-b"}:
        side = "a" if move == "light-a" else "b"
        if state["lit"] is not None or state[side] < 2:
            state["rejected"] += 1
            state["notes"].append(f"rejected {move}: lit {state['lit']} wax {state[side]}")
            return state
        state["lit"] = side
        state[side] -= 1
    elif move == "pass":
        if state["lit"] is None:
            state["rejected"] += 1
            state["notes"].append("rejected pass: dark")
            return state
        other = "b" if state["lit"] == "a" else "a"
        if state[other] < 2:
            state["rejected"] += 1
            state["notes"].append(f"rejected pass: partner wax {state[other]}")
            return state
        state[state["lit"]] -= 1
        state[other] -= 1
        state["lit"] = other
        state["passes"] += 1
    elif move == "snuff":
        if state["lit"] is None:
            state["rejected"] += 1
            state["notes"].append("rejected snuff: already dark")
            return state
        state["lit"] = None
    else:
        if state["lit"] is not None:
            state[state["lit"]] -= 1
    state["turn"] += 1
    state["accepted"] += 1
    if state["a"] <= 0 or state["b"] <= 0:
        state["a"] = max(state["a"], 0)
        state["b"] = max(state["b"], 0)
        state["lit"] = None
        state["done"] = True
    return state

def show(state):
    print(f"the-weir {state['seed']}")
    print(f"a {state['a']}  b {state['b']}  lit {state['lit']}  passes {state['passes']}")
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
    if s["a"] != WAX or s["lit"] is not None:
        fails.append("fresh")
    s = replay("solo", ["light-a"])
    if s["lit"] != "a" or s["b"] != WAX or s["passes"] != 0:
        fails.append("solo light does not light the partner")
    s = replay("both", ["light-a", "pass"])
    if s["lit"] != "b" or s["passes"] != 1 or s["a"] != 2 or s["b"] != 3:
        fails.append(f"pass should spend both and move the flame: {s}")
    s = replay("thin", ["light-a", "hold", "hold", "pass"])
    if s["rejected"] != 1 or s["passes"] != 0 or s["lit"] != "a":
        fails.append("pass on a thin partner must be rejected")
    s = replay("dark", ["pass"])
    if s["rejected"] != 1 or s["accepted"] != 0:
        fails.append("dark pass")
    s = replay("spent", ["light-a", "hold", "hold", "hold"])
    if not s["done"] or s["a"] != 0:
        fails.append("spent at 0")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        return 1
    print("PASS")
    print("solo light stays on a; pass moves the flame; thin partner rejected")
    return 0

def main(argv):
    p = argparse.ArgumentParser(description="The Weir")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("check")
    sh = sub.add_parser("show")
    sh.add_argument("seed")
    rp = sub.add_parser("replay")
    rp.add_argument("seed")
    rp.add_argument("moves")
    args = p.parse_args(argv)
    if args.cmd == "check" or args.cmd is None:
        return check()
    if args.cmd == "show":
        show(fresh(args.seed))
        return 0
    lines = open(args.moves).read().splitlines()
    show(replay(args.seed, lines))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
