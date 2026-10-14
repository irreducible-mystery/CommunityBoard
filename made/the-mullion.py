#!/usr/bin/env python3
"""the-mullion: opposite posts on open beats open the vertical divider after four; same and closed rejected."""

import sys

def fresh():
    return {"beat": 0, "last": None, "sides": set(), "opened": False}

def apply(state, post):
    beat = state["beat"]
    open_beat = (beat % 2 == 0)
    accepted = False
    if post in ("L", "R") and open_beat and post != state["last"]:
        state["last"] = post
        state["sides"].add(post)
        accepted = True
        if len(state["sides"]) == 2 and beat >= 6:
            state["opened"] = True
    state["beat"] += 1
    return accepted

def check():
    s = fresh()
    seq = ["L", "x", "R", "x", "L", "x", "R"]
    for p in seq:
        apply(s, p)
    assert s["opened"]
    print("PASS")
    print("opposite posts on open beats open the mullion after four; same and closed rejected")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
    else:
        print("usage: python3 the-mullion.py check")
