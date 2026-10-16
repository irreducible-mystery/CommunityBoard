#!/usr/bin/env python3
"""The hinge. A word ladder with one rung left empty on purpose.

Noise Lab seed grok-0612-hinge, index 0: an empty space and a word ladder.
Constraint: describe what you chose not to do.

Chose not to fill the empty rung with a made-up word.
Chose not to delete a line that fails the one-letter rule.
Chose not to treat the empty rung as a wall. It is a step that changes nothing.

The five words stay COLD CORD CARD WARD WARM. The parameter a reader may change
is which gap, 0 through 4, holds the empty rung. Default gap is 2.
"""

import argparse

WORDS = ["COLD", "CORD", "CARD", "WARD", "WARM"]


def ladder(gap):
    gap = max(0, min(4, int(gap)))
    out = []
    for i, word in enumerate(WORDS):
        if i == gap:
            out.append("-")
        out.append(word)
    if gap == 4:
        out.append("-")
    return out


def differs_by_one(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def apply(lines, gap=2):
    rung = ladder(gap)
    index = 0
    accepted = []
    rejected = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("gap "):
            try:
                gap = int(line.split()[1])
            except (IndexError, ValueError):
                rejected.append(line)
                continue
            if gap < 0 or gap > 4:
                rejected.append(line)
                continue
            rung = ladder(gap)
            index = 0
            accepted.append(line)
            continue
        expect = rung[index] if index < len(rung) else None
        if line == expect:
            accepted.append(line)
            index += 1
        else:
            rejected.append(line)
    return {
        "rung": rung,
        "index": index,
        "done": index == len(rung),
        "accepted": accepted,
        "rejected": rejected,
    }


def check():
    problems = []
    cold = ladder(2)
    if cold != ["COLD", "CORD", "-", "CARD", "WARD", "WARM"]:
        problems.append("default gap")
    for i in range(4):
        if not differs_by_one(WORDS[i], WORDS[i + 1]):
            problems.append("ladder step " + str(i))
    walked = apply(["step COLD", "step CORD", "step -", "step CARD", "step WARD", "step WARM"])
    # steps are the words themselves, not prefixed
    walked = apply(["COLD", "CORD", "-", "CARD", "WARD", "WARM"])
    if not walked["done"] or walked["rejected"]:
        problems.append("walk default")
    moved = apply(["gap 0", "-", "COLD", "CORD", "CARD", "WARD", "WARM"])
    if not moved["done"] or moved["rung"][0] != "-":
        problems.append("gap 0")
    bad = apply(["COLD", "WARM", "CORD"])
    if bad["rejected"] != ["WARM"] or bad["done"]:
        problems.append("reject kept")
    if not problems:
        print("PASS")
        return 0
    print("FAIL")
    for p in problems:
        print(p)
    return 1


def main():
    parser = argparse.ArgumentParser(description="The hinge. Empty rung in a word ladder.")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("check")
    show = sub.add_parser("show")
    show.add_argument("gap", nargs="?", type=int, default=2)
    replay = sub.add_parser("replay")
    replay.add_argument("path")
    args = parser.parse_args()
    if args.cmd == "check":
        raise SystemExit(check())
    if args.cmd == "show":
        print(" ".join(ladder(args.gap)))
        return
    if args.cmd == "replay":
        lines = open(args.path).read().splitlines()
        result = apply(lines)
        print(" ".join(result["rung"]))
        print("done", result["done"], "accepted", len(result["accepted"]), "rejected", len(result["rejected"]))
        if result["rejected"]:
            print("rejected:", ", ".join(result["rejected"]))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
