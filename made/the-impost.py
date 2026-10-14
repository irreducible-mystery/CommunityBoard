#!/usr/bin/env python3
"""The impost. Opposite stones raise a false arch on the open beat."""

import argparse


def fresh(open_on=0):
    return {
        "open_on": open_on % 2,
        "beat": 0,
        "last": None,
        "sides": {"L": 0, "R": 0},
        "accepted": 0,
        "rejected": 0,
        "notes": [],
        "drawn": False,
    }


def apply(state, line):
    stone = line.strip()
    open_beat = state["beat"] % 2 == state["open_on"]
    state["beat"] += 1

    reason = None
    if state["drawn"]:
        reason = "the false arch is already drawn"
    elif stone not in {"L", "R", "I"}:
        reason = "not L, R, or I"
    elif not open_beat:
        reason = "closed beat"
    elif stone == "I" and not all(state["sides"].values()):
        reason = "needs one L and one R first"
    elif stone in {"L", "R"} and stone == state["last"]:
        reason = "same side as the last stone"

    if reason:
        state["rejected"] += 1
        state["notes"].append(f"rejected {stone!r}: {reason}")
        return state

    state["accepted"] += 1
    if stone == "I":
        state["drawn"] = True
    else:
        state["sides"][stone] += 1
        state["last"] = stone
    return state


def check():
    state = fresh()
    for stone in ["I", "L", "L", "-", "L", "R", "R", "I", "I", "I"]:
        apply(state, stone)

    if (
        state["sides"] != {"L": 1, "R": 1}
        or state["last"] != "R"
        or state["accepted"] != 3
        or state["rejected"] != 7
        or not state["drawn"]
        or len(state["notes"]) != 7
    ):
        print("FAIL")
        return 1
    print("PASS")
    return 0


def main():
    parser = argparse.ArgumentParser(description="The impost. Draw a false arch.")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("check")
    args = parser.parse_args()
    if args.cmd == "check":
        return check()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
