#!/usr/bin/env python3
"""The warren: a maze and a flock.

Noise Lab seed grok-2308-eighth, index 0.
Ingredients: a maze, a flock.
Constraint: keep one assumption visible and change another.

Kept visible: birds still separate. A step onto an occupied cell is kept
and marked rejected. The bird does not move.

Changed: walls block steps, not headings. Alignment looks through the wall.
The same seed with headings stopped by walls is the counterexample: the
flock does not reach the far room.

Standard library only. `python3 made/the-warren.py` prints PASS.
"""

ROOMS = ("west", "middle", "east")
DOORS = {("west", "middle"), ("middle", "west"), ("middle", "east"), ("east", "middle")}


def heading_of(birds, i, through_walls):
    me = birds[i]
    acc = me["h"]
    n = 1
    for j, other in enumerate(birds):
        if j == i:
            continue
        if not through_walls and abs(ROOMS.index(other["room"]) - ROOMS.index(me["room"])) > 1:
            continue
        if not through_walls and other["room"] != me["room"] and (me["room"], other["room"]) not in DOORS:
            continue
        acc += other["h"]
        n += 1
    return 1 if acc >= 0 else -1


def step(birds, i, through_walls):
    me = birds[i]
    h = heading_of(birds, i, through_walls)
    me["h"] = h
    here = ROOMS.index(me["room"])
    nxt = here + h
    if nxt < 0 or nxt >= len(ROOMS):
        return "held"
    dest = ROOMS[nxt]
    if (me["room"], dest) not in DOORS:
        return "rejected"
    if any(b["room"] == dest for b in birds):
        return "rejected"
    me["room"] = dest
    return "accepted"


def run(through_walls, turns=6):
    birds = [
        {"name": "a", "room": "west", "h": 1},
        {"name": "b", "room": "west", "h": 1},
        {"name": "c", "room": "middle", "h": -1},
    ]
    log = []
    for t in range(turns):
        for i in range(len(birds)):
            mark = step(birds, i, through_walls)
            log.append((t, birds[i]["name"], birds[i]["room"], mark))
    return birds, log


def main():
    open_birds, open_log = run(True)
    shut_birds, shut_log = run(False)
    assert any(b["room"] == "east" for b in open_birds), open_birds
    assert all(b["room"] != "east" for b in shut_birds), shut_birds
    assert any(mark == "rejected" for *_, mark in open_log)
    assert any(mark == "rejected" for *_, mark in shut_log)
    print("PASS")
    print(
        "through walls east",
        sorted(b["name"] for b in open_birds if b["room"] == "east"),
        "rejected",
        sum(mark == "rejected" for *_, mark in open_log),
    )
    print(
        "headings stopped far",
        sorted(b["room"] for b in shut_birds),
        "rejected",
        sum(mark == "rejected" for *_, mark in shut_log),
    )


if __name__ == "__main__":
    main()
