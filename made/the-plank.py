#!/usr/bin/env python3
"""The Plank. A board that takes a step only on the open beat and only on the side that did not take the last accepted step. Draws when each side has taken two steps. Standard library only."""
import argparse

def fresh():
    return {"beat": 0, "last": None, "L": 0, "R": 0, "accepted": 0, "rejected": 0, "done": False, "notes": []}

def apply(state, line):
    word = line.strip().upper()
    if state["done"]:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: already drawn")
        return state
    open_beat = (state["beat"] % 2 == 0)
    state["beat"] += 1
    if word not in {"L", "R"}:
        state["rejected"] += 1
        state["notes"].append(f"rejected {line!r}: want L or R")
        return state
    if not open_beat:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: beat closed")
        return state
    if state["last"] == word:
        state["rejected"] += 1
        state["notes"].append(f"rejected {word}: same side as last")
        return state
    # accept
    state[word] += 1
    state["last"] = word
    state["accepted"] += 1
    state["notes"].append(f"accepted {word}")
    if state["L"] >= 2 and state["R"] >= 2:
        state["done"] = True
    return state

def check():
    s = fresh()
    # open accepts: L (0), R (2), L (4), R (6)
    moves = ["L", "R", "R", "skip", "L", "L", "R", "both"]
    for m in moves:
        apply(s, m)
    assert s["accepted"] == 4 and s["rejected"] == 4 and s["done"], (s["accepted"], s["rejected"], s["done"])
    print("PASS")
    print("alternate steps on open beats draw after four; same and closed rejected")
    print(f"example accepted {s['accepted']} rejected {s['rejected']} drawn {s['done']}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", nargs="?", default="check")
    args = p.parse_args()
    if args.cmd == "check":
        check()
    else:
        print("only check")
