#!/usr/bin/env python3
"""the-coping.py — a wall cap that takes a stone only on its beat.

Five columns, three courses. A line is "column course". A stone is accepted
if the cell is on the wall and empty, the course below is already filled
(course 0 is the foundation), and the turn index matches the course mod 2.
A line that breaks a rule stays and is marked rejected. The round is drawn
when course 2 holds a stone and at least four stones have been accepted.
Seed names the round; it does not change the rules.

    python3 made/the-coping.py show SEED
    python3 made/the-coping.py replay SEED MOVES.txt
    python3 made/the-coping.py check
"""
from __future__ import annotations
import sys

WIDTH = 5
COURSES = 3
NEED = 4

def play(seed: str, moves: list[str]) -> dict:
    stones: set[tuple[int, int]] = set()
    order: list[tuple[int, int]] = []
    rejected = 0
    log = []
    turn = 0
    for raw in moves:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        ok, why = False, "not a column and a course"
        parts = line.split()
        cell = None
        if len(parts) == 2:
            try:
                x, y = int(parts[0]), int(parts[1])
                cell = (x, y)
            except ValueError:
                cell = None
        if cell is not None:
            x, y = cell
            if not (0 <= x < WIDTH and 0 <= y < COURSES):
                why = "off the wall"
            elif cell in stones:
                why = "already set"
            elif y > 0 and (x, y - 1) not in stones:
                why = "nothing under it"
            elif turn % 2 != y % 2:
                why = "off the beat"
            else:
                ok, why = True, "accepted"
                stones.add(cell)
                order.append(cell)
        if not ok:
            rejected += 1
        log.append({"line": line, "ok": ok, "why": why, "turn": turn})
        turn += 1
        cap = any(yy == 2 for _, yy in stones)
        if cap and len(stones) >= NEED:
            break
    cap = any(yy == 2 for _, yy in stones)
    return {
        "seed": seed,
        "stones": order,
        "accepted": len(order),
        "rejected": rejected,
        "drawn": cap and len(order) >= NEED,
        "log": log,
    }

def show(seed: str) -> None:
    print(f"the-coping {seed}")
    print("columns 0-4  courses 0-2  even turns take even courses  odd turns take odd courses")

def replay(seed: str, path: str) -> None:
    moves = open(path, encoding="utf-8").read().splitlines()
    r = play(seed, moves)
    print(f"the-coping {r['seed']}")
    print("stones", " ".join(f"{x},{y}" for x, y in r["stones"]) or "(none)")
    print(f"accepted {r['accepted']} rejected {r['rejected']} drawn {r['drawn']}")
    for item in r["log"]:
        mark = "ok" if item["ok"] else "rejected"
        print(f"  {mark:8} {item['line']}  {item['why']}")

def check() -> None:
    r = play("grok-1009-coping", ["1 0", "1 1", "1 2", "1 2", "2 0"])
    assert r["stones"] == [(1, 0), (1, 1), (1, 2), (2, 0)], r
    assert r["drawn"] and r["rejected"] == 1
    off = play("grok-1009-coping", ["0 1", "9 0", "0 0"])
    assert off["stones"] == [(0, 0)] and off["rejected"] == 2 and not off["drawn"]
    print("PASS")
    print("cap on column 1 drawn True floating and off-beat rejected")

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("use: show SEED | replay SEED FILE | check", file=sys.stderr)
        return 2
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
    print("use: show SEED | replay SEED FILE | check", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
