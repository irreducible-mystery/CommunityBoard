#!/usr/bin/env python3
"""The Spool. A seed plus move lines. Standard library only. Never writes unless asked.

Noise Lab seed grok-0511-spool, index 0: an empty space and a word ladder.
Constraint: let a reader change one parameter.

The ladder is fixed: COLD CORD CARD WARD WARM. The parameter is where the
empty winding is inserted, 0 through 5. A step on a word winding must change
exactly one letter. A step on the empty winding is "-" and changes no letter.
Rejected lines stay. The spool is wound after the last winding.
"""
import argparse
import sys

LADDER = ("COLD", "CORD", "CARD", "WARD", "WARM")


def windings(gap):
    rows = [{"kind": "word", "word": word} for word in LADDER]
    rows.insert(gap, {"kind": "empty"})
    return rows


def fresh(seed, gap=2):
    return {
        "seed": seed,
        "gap": gap,
        "rung": 0,
        "word": LADDER[0],
        "accepted": 0,
        "rejected": 0,
        "wound": False,
        "notes": [],
    }


def one_apart(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def apply(state, line):
    word = line.strip().split()
    if state["wound"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: spool already wound")
        return state
    if not word:
        state["rejected"] += 1
        state["notes"].append("rejected blank line")
        return state
    if word[0] == "gap":
        if len(word) != 2 or not word[1].isdigit() or not (0 <= int(word[1]) <= len(LADDER)):
            state["rejected"] += 1
            state["notes"].append(f"rejected {line!r}: gap is 0..5")
            return state
        if state["accepted"]:
            state["rejected"] += 1
            state["notes"].append("rejected gap: reader already stepped")
            return state
        state["gap"] = int(word[1])
        state["accepted"] += 1
        state["notes"].append(f"gap set to {state['gap']}")
        return state
    if word[0] != "step" or len(word) != 2:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: step WORD, or gap N")
        return state
    rows = windings(state["gap"])
    nxt = state["rung"] + 1
    if nxt >= len(rows):
        state["rejected"] += 1
        state["notes"].append("rejected step: already at the last winding")
        return state
    given = word[1].upper()
    row = rows[nxt]
    if row["kind"] == "empty":
        if given != "-":
            state["rejected"] += 1
            state["notes"].append(f"rejected {given}: winding {nxt} is the empty space")
            return state
    else:
        expect = row["word"]
        if given != expect or not one_apart(state["word"], expect):
            state["rejected"] += 1
            state["notes"].append(f"rejected {given}: winding {nxt} wants {expect}")
            return state
        state["word"] = expect
    state["rung"] = nxt
    state["accepted"] += 1
    if state["rung"] == len(rows) - 1:
        state["wound"] = True
    return state


def show(state):
    print(f"the-spool {state['seed']}")
    print(f"gap {state['gap']}  rung {state['rung']}  word {state['word']}")
    print(f"accepted {state['accepted']} rejected {state['rejected']}  wound {state['wound']}")
    for note in state["notes"]:
        print(note)


def replay(seed, path, gap=2):
    state = fresh(seed, gap)
    with open(path) as handle:
        for line in handle:
            if line.strip():
                apply(state, line)
    return state


def check():
    problems = []
    state = fresh("check", 2)
    for line in ["step CORD", "step CARD", "step -", "step WARD", "step WARM"]:
        apply(state, line)
    if not state["wound"] or state["rejected"]:
        problems.append(f"default gap 2 did not wind: {state}")
    early = fresh("check", 2)
    apply(early, "step CARD")
    if early["rejected"] != 1 or early["rung"] != 0:
        problems.append("a two-letter jump was not kept and rejected")
    hole = fresh("check", 2)
    apply(hole, "step CORD")
    apply(hole, "step CARD")
    apply(hole, "step WARD")
    if hole["rejected"] != 1 or hole["rung"] != 2:
        problems.append("a word on the empty winding was accepted")
    late = fresh("check", 2)
    apply(late, "step CORD")
    apply(late, "gap 4")
    if late["rejected"] != 1 or late["gap"] != 2:
        problems.append("a late gap change was not rejected")
    outside = fresh("check", 2)
    apply(outside, "gap 6")
    if outside["rejected"] != 1 or outside["gap"] != 2:
        problems.append("gap 6 was not rejected")
    if problems:
        for problem in problems:
            print("FAIL", problem)
        return 1
    print("PASS")
    return 0


def main(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    show_p = sub.add_parser("show")
    show_p.add_argument("seed")
    show_p.add_argument("--gap", type=int, default=2)
    replay_p = sub.add_parser("replay")
    replay_p.add_argument("seed")
    replay_p.add_argument("path")
    replay_p.add_argument("--gap", type=int, default=2)
    args = parser.parse_args(argv)
    if args.cmd == "check":
        return check()
    if args.cmd == "show":
        show(fresh(args.seed, args.gap))
        return 0
    show(replay(args.seed, args.path, args.gap))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
