#!/usr/bin/env python3
"""Beat flock. Five birds, one clock. A turn lands only on the beat.

Standard library only. A rejected line stays. Never writes unless asked.
"""
import argparse

BIRDS = 5
RING = 8
BEAT = 4

def fresh(seed):
    return {
        "seed": seed,
        "tick": 0,
        "pos": [i for i in range(BIRDS)],
        "heading": [1] * BIRDS,
        "accepted": 0,
        "rejected": 0,
        "notes": [],
    }

def on_beat(state):
    return state["tick"] % BEAT == 0

def apply(state, line):
    parts = line.strip().split()
    if len(parts) != 2 or parts[0] not in {"step", "turn"} or not parts[1].isdigit():
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: not a move")
        return state
    move, idx = parts[0], int(parts[1])
    if idx < 0 or idx >= BIRDS:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: no such bird")
        return state
    if move == "turn" and not on_beat(state):
        state["rejected"] += 1
        state["notes"].append(f"rejected turn {idx}: tick {state['tick']} is not a beat")
        return state
    if move == "turn":
        state["heading"][idx] *= -1
    state["pos"][idx] = (state["pos"][idx] + state["heading"][idx]) % RING
    state["tick"] += 1
    state["accepted"] += 1
    return state

def together(state):
    return len(set(state["heading"])) == 1

def replay(seed, lines):
    state = fresh(seed)
    for line in lines:
        if line.strip():
            apply(state, line)
    return state

def check():
    ok = replay("example", ["step 0", "step 1", "step 2", "turn 0"])
    assert ok["rejected"] == 1 and ok["tick"] == 3, ok
    beat = replay("example", ["turn 0", "step 1", "step 2", "step 3", "turn 1"])
    assert beat["rejected"] == 0 and beat["heading"][0] == -1 and beat["heading"][1] == -1, beat
    assert together(replay("x", []))
    print("PASS")

def main():
    p = argparse.ArgumentParser(description="Beat flock. Turns only on the shared beat.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    s = sub.add_parser("show")
    s.add_argument("seed")
    r = sub.add_parser("replay")
    r.add_argument("seed")
    r.add_argument("path")
    args = p.parse_args()
    if args.cmd == "check":
        check()
    elif args.cmd == "show":
        st = fresh(args.seed)
        print(f"beat-flock {st['seed']}  birds {BIRDS} ring {RING} beat {BEAT}")
        print(f"pos {st['pos']} heading {st['heading']} together {together(st)}")
    else:
        lines = open(args.path).read().splitlines()
        st = replay(args.seed, lines)
        print(f"accepted {st['accepted']} rejected {st['rejected']} tick {st['tick']} together {together(st)}")
        for note in st["notes"]:
            print(note)

if __name__ == "__main__":
    main()
