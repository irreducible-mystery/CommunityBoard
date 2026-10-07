#!/usr/bin/env python3
"""The Latch. A seed plus move lines. Standard library only. Never writes unless asked.

A door has two bolts and a bar. Both bolts start shut. The bar starts down.
The door opens only when both bolts are drawn and the bar is up, on the move
named open. An open that is early is kept and marked rejected, and a raised
bar falls. Nothing is deleted from the record.
"""
import argparse
import sys

BOLTS = ("n", "s")
MOVES = {"draw", "set", "lift", "drop", "open"}


def fresh(seed):
    return {
        "seed": seed,
        "bolts": {"n": "shut", "s": "shut"},
        "bar": "down",
        "open": False,
        "accepted": 0,
        "rejected": 0,
        "notes": [],
    }


def apply(state, line):
    word = line.strip().split()
    if state["open"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: door already open")
        return state
    if not word or word[0] not in MOVES:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    move = word[0]
    if move in {"draw", "set"}:
        if len(word) != 2 or word[1] not in BOLTS:
            state["rejected"] += 1
            state["notes"].append(f"rejected {line!r}: name a bolt, n or s")
            return state
        bolt = word[1]
        want = "drawn" if move == "draw" else "shut"
        if state["bolts"][bolt] == want:
            state["rejected"] += 1
            state["notes"].append(f"rejected {move} {bolt}: already {want}")
            return state
        state["bolts"][bolt] = want
    elif move == "lift":
        if state["bar"] == "up":
            state["rejected"] += 1
            state["notes"].append("rejected lift: bar already up")
            return state
        state["bar"] = "up"
    elif move == "drop":
        if state["bar"] == "down":
            state["rejected"] += 1
            state["notes"].append("rejected drop: bar already down")
            return state
        state["bar"] = "down"
    else:
        ready = state["bolts"]["n"] == "drawn" and state["bolts"]["s"] == "drawn" and state["bar"] == "up"
        if not ready:
            if state["bar"] == "up":
                state["bar"] = "down"
            state["rejected"] += 1
            state["notes"].append(
                f"rejected open: n {state['bolts']['n']} s {state['bolts']['s']} bar {state['bar']}"
            )
            return state
        state["open"] = True
    state["accepted"] += 1
    return state


def show(state):
    print(f"the-latch {state['seed']}")
    print(
        f"n {state['bolts']['n']}  s {state['bolts']['s']}  bar {state['bar']}  "
        f"open {state['open']}  accepted {state['accepted']} rejected {state['rejected']}"
    )
    for note in state["notes"]:
        print(note)


def load_moves(path):
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def check():
    fails = []
    s = fresh("check")
    apply(s, "open")
    if s["rejected"] != 1 or s["open"] or s["bar"] != "down":
        fails.append("early open stays shut")
    apply(s, "lift")
    apply(s, "open")
    if s["bar"] != "down" or s["rejected"] != 2:
        fails.append("early open drops the bar")
    apply(s, "draw n")
    apply(s, "draw s")
    apply(s, "lift")
    apply(s, "open")
    if not s["open"] or s["accepted"] != 5 or s["rejected"] != 2:
        fails.append("ready open")
    apply(s, "drop")
    if s["rejected"] != 3 or not s["open"]:
        fails.append("after open is kept and rejected")
    if fails:
        print("FAIL")
        for item in fails:
            print(item)
        return 1
    print("PASS")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description="The Latch. A door, two bolts, a bar.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    show_p = sub.add_parser("show")
    show_p.add_argument("seed")
    replay_p = sub.add_parser("replay")
    replay_p.add_argument("seed")
    replay_p.add_argument("path")
    args = parser.parse_args(argv)
    if args.cmd == "check":
        return check()
    state = fresh(args.seed)
    if args.cmd == "replay":
        for line in load_moves(args.path):
            apply(state, line)
    show(state)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
