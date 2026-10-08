#!/usr/bin/env python3
"""the-notch.py — a stick that remembers where it was cut.

Length 7, positions 0 through 6. A notch is accepted if the position is on the
stick, empty, and not next to the last accepted notch. The first notch has no
neighbour to avoid. A line that breaks a rule stays and is marked rejected.
The round is spent at three accepted notches. Seed names the round; it does
not change the rules.

    python3 made/the-notch.py show SEED
    python3 made/the-notch.py replay SEED MOVES.txt
    python3 made/the-notch.py check
"""
from __future__ import annotations
import sys

LENGTH = 7
NEED = 3

def play(seed: str, moves: list[str]) -> dict:
    notches: list[int] = []
    rejected = 0
    log = []
    for raw in moves:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        ok, why = False, "not an integer position"
        try:
            pos = int(line)
        except ValueError:
            pos = None
        if pos is not None:
            if not 0 <= pos < LENGTH:
                why = "off the stick"
            elif pos in notches:
                why = "already notched"
            elif notches and abs(pos - notches[-1]) <= 1:
                why = "beside the last notch"
            else:
                ok, why = True, "accepted"
                notches.append(pos)
        if not ok:
            rejected += 1
        log.append({"line": line, "ok": ok, "why": why})
        if len(notches) >= NEED:
            break
    return {
        "seed": seed,
        "notches": notches,
        "accepted": len(notches),
        "rejected": rejected,
        "spent": len(notches) >= NEED,
        "log": log,
    }

def show(seed: str) -> None:
    print(f"the-notch {seed}")
    print("positions 0-6  need 3  no two accepted notches adjacent in the record order")

def replay(seed: str, path: str) -> None:
    moves = open(path, encoding="utf-8").read().splitlines()
    r = play(seed, moves)
    print(f"the-notch {r['seed']}")
    print("notches", " ".join(map(str, r["notches"])) or "(none)")
    print(f"accepted {r['accepted']} rejected {r['rejected']} spent {r['spent']}")
    for item in r["log"]:
        mark = "ok" if item["ok"] else "rejected"
        print(f"  {mark:8} {item['line']}  {item['why']}")

def check() -> None:
    r = play("grok-2005-sill", ["0", "1", "3", "3", "6"])
    assert r["notches"] == [0, 3, 6], r
    assert r["rejected"] == 2 and r["spent"]
    off = play("grok-2005-sill", ["7", "-1", "2"])
    assert off["notches"] == [2] and off["rejected"] == 2
    print("PASS")
    print("route 0 3 6 done True beside and repeat rejected")

def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd == "check":
        check()
        return 0
    if cmd == "show" and len(argv) == 3:
        show(argv[2])
        return 0
    if cmd == "replay" and len(argv) == 4:
        replay(argv[2], argv[3])
        return 0
    print(__doc__)
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
