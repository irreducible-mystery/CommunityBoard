#!/usr/bin/env python3
"""The Weir. Two streams and a gate that opens only when they agree on the beat.

Off the beat, a move sets a stream: `left a`, `right b`, or `both a`.
On the beat, the only accepted move is `agree X`, and only if both streams
hold X. A line that breaks a rule stays and is marked rejected; the turn
does not advance. The round is drawn at three passes.

The seed names the round. It does not change the rules.

    python3 made/the-weir.py show SEED
    python3 made/the-weir.py replay SEED MOVES.txt
    python3 made/the-weir.py check

Standard library only. Never writes unless asked.
"""
import argparse
import sys

PASSES = 3
LETTERS = set("abc")

def fresh(seed):
    return {"seed": seed, "left": None, "right": None, "turn": 0,
            "passes": 0, "accepted": 0, "rejected": 0, "done": False, "notes": []}

def on_beat(state):
    return state["turn"] % 2 == 1

def apply(state, line):
    word = line.strip().split()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: weir already drawn")
        return state
    if len(word) != 2 or word[0] not in {"left", "right", "both", "agree"} or word[1] not in LETTERS:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    kind, letter = word
    beat = on_beat(state)
    if kind == "agree":
        if not beat:
            state["rejected"] += 1
            state["notes"].append("rejected agree: off the beat")
            return state
        if state["left"] != letter or state["right"] != letter:
            state["rejected"] += 1
            state["notes"].append(
                f"rejected agree {letter}: left {state['left']} right {state['right']}")
            return state
        state["passes"] += 1
        state["accepted"] += 1
        state["turn"] += 1
        state["notes"].append(f"ok agree {letter}")
        if state["passes"] >= PASSES:
            state["done"] = True
        return state
    if beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {kind}: the beat wants an agreement")
        return state
    if kind == "both":
        state["left"] = letter
        state["right"] = letter
    else:
        state[kind] = letter
    state["accepted"] += 1
    state["turn"] += 1
    state["notes"].append(f"ok {kind} {letter}")
    return state

def replay(seed, lines):
    state = fresh(seed)
    for line in lines:
        if line.strip():
            apply(state, line)
    return state

def show(state):
    print(f"the-weir {state['seed']}")
    print(f"left {state['left']}  right {state['right']}  beat {on_beat(state)}")
    print(
        f"passes {state['passes']}/{PASSES}  accepted {state['accepted']} "
        f"rejected {state['rejected']}  drawn {state['done']}"
    )
    for note in state["notes"]:
        print(note)

def check():
    drawn = replay("check-drawn", [
        "both a", "agree a",
        "left b", "agree b",          # right still a, reject, still on beat
        "agree a",                    # right still a, but left is b, reject
        "both c", "agree c",          # still on the beat, both rejected
        "agree c",                    # already drawn? no, stuck
    ])
    # The mismatch above is the counterexample: one stream changed, the beat
    # cannot set the other, and agree cannot invent the missing letter.
    assert not drawn["done"] and drawn["passes"] == 1 and drawn["rejected"] == 5, drawn
    drawn = replay("check-drawn-ok", [
        "both a", "agree a",
        "both b", "agree b",
        "both c", "agree c",
        "agree c",
    ])
    assert drawn["done"] and drawn["passes"] == 3 and drawn["rejected"] == 1, drawn
    trap = replay("check-trap", ["left a", "right a"])
    assert trap["rejected"] == 1 and trap["turn"] == 1 and not trap["done"], trap
    bad = replay("check-bad", ["agree a", "neither z", "both a"])
    assert bad["rejected"] == 2 and bad["accepted"] == 1, bad
    print("PASS")
    print(f"drawn passes {drawn['passes']} rejected {drawn['rejected']}")
    print("mismatch stayed on the beat")
    print(f"trap turn {trap['turn']} rejected {trap['rejected']}")
    return 0

def main(argv):
    parser = argparse.ArgumentParser(description="The Weir")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("show")
    p.add_argument("seed")
    p = sub.add_parser("replay")
    p.add_argument("seed")
    p.add_argument("moves")
    args = parser.parse_args(argv)
    if args.cmd == "check":
        return check()
    if args.cmd == "show":
        show(fresh(args.seed))
        return 0
    with open(args.moves, encoding="utf-8") as handle:
        show(replay(args.seed, handle))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
