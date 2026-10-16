#!/usr/bin/env python3
"""Tide maze: a maze you may only enter on the beat.

A reader can change one parameter, the period. Steps that miss the beat are
kept and marked rejected. The walker does not move. No network, stdlib only.
"""

from __future__ import annotations

import random
import sys

PERIOD = 4
W, H = 9, 9


def carve(seed: str, w: int = W, h: int = H):
    rng = random.Random(seed)
    # walls between cells: h_walls[y][x] is the south wall of (x, y), except last row
    visited = [[False] * w for _ in range(h)]
    h_open = [[False] * w for _ in range(h - 1)]
    v_open = [[False] * (w - 1) for _ in range(h)]

    def walk(x, y):
        visited[y][x] = True
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        rng.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h) or visited[ny][nx]:
                continue
            if dx == 1:
                v_open[y][x] = True
            elif dx == -1:
                v_open[y][x - 1] = True
            elif dy == 1:
                h_open[y][x] = True
            else:
                h_open[y - 1][x] = True
            walk(nx, ny)

    walk(0, 0)
    return h_open, v_open


def can_step(h_open, v_open, x, y, dx, dy):
    nx, ny = x + dx, y + dy
    if not (0 <= nx < W and 0 <= ny < H):
        return False
    if dx == 1:
        return v_open[y][x]
    if dx == -1:
        return v_open[y][x - 1]
    if dy == 1:
        return h_open[y][x]
    if dy == -1:
        return h_open[y - 1][x]
    return False


DIRS = {"n": (0, -1), "e": (1, 0), "s": (0, 1), "w": (-1, 0)}


def play(seed: str, lines, period: int = PERIOD):
    h_open, v_open = carve(seed)
    x = y = 0
    beat = 0
    accepted = rejected = 0
    record = []
    for raw in lines:
        line = raw.strip().lower()
        if not line:
            continue
        if line not in DIRS:
            rejected += 1
            record.append({"line": raw, "status": "rejected", "why": "not a step"})
            continue
        dx, dy = DIRS[line]
        nx, ny = x + dx, y + dy
        on_beat = (beat % period) == ((x + y) % period)
        open_wall = can_step(h_open, v_open, x, y, dx, dy)
        if open_wall and on_beat:
            x, y = nx, ny
            beat += 1
            accepted += 1
            record.append({"line": line, "status": "accepted", "at": [x, y], "beat": beat})
        else:
            rejected += 1
            why = "wall" if not open_wall else "off beat"
            record.append({"line": line, "status": "rejected", "why": why, "at": [x, y], "beat": beat})
    return {
        "seed": seed,
        "period": period,
        "at": [x, y],
        "beat": beat,
        "accepted": accepted,
        "rejected": rejected,
        "done": [x, y] == [W - 1, H - 1],
        "record": record,
    }


def route(seed: str, period: int = PERIOD):
    """Breadth-first path that leaves a cell only on its beat."""
    h_open, v_open = carve(seed)
    start = (0, 0, 0)
    prev = {start: None}
    queue = [start]
    goal = None
    while queue:
        x, y, phase = queue.pop(0)
        if (x, y) == (W - 1, H - 1):
            goal = (x, y, phase)
            break
        if phase != ((x + y) % period):
            continue
        for name, (dx, dy) in DIRS.items():
            if not can_step(h_open, v_open, x, y, dx, dy):
                continue
            nxt = (x + dx, y + dy, (phase + 1) % period)
            if nxt not in prev:
                prev[nxt] = (x, y, phase, name)
                queue.append(nxt)
    if goal is None:
        return []
    lines = []
    cur = goal
    while prev[cur] is not None:
        x, y, beat, name = prev[cur]
        lines.append(name)
        cur = (x, y, beat)
    lines.reverse()
    return lines


def check():
    seed = "grok-1705-tide"
    lines = route(seed, PERIOD)
    result = play(seed, lines, PERIOD)
    assert result["accepted"] == len(lines) and result["rejected"] == 0, result
    assert result["done"], result
    bad = play(seed, ["n"], PERIOD)
    assert bad["rejected"] == 1 and bad["at"] == [0, 0] and bad["accepted"] == 0, bad
    # a reader changes the period; the same first step may no longer fit
    other = play(seed, lines[:1], period=3)
    assert other["period"] == 3
    # rejected lines stay in the record
    assert bad["record"][0]["status"] == "rejected"
    print("PASS")
    print(f"route {len(lines)} steps, done={result['done']}, off-beat north rejected")
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "check":
        return check()
    seed = argv[1] if len(argv) > 1 else "grok-1705-tide"
    period = int(argv[2]) if len(argv) > 2 else PERIOD
    lines = [ln for ln in sys.stdin]
    result = play(seed, lines, period)
    print(
        f"at {result['at']} beat {result['beat']} accepted {result['accepted']} "
        f"rejected {result['rejected']} done {result['done']}"
    )
    for row in result["record"]:
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
