"""The blank: a word ladder with one empty cell.

Invitation grok-1905-blank, index 0: a word ladder and an empty space.
Constraint: describe what you chose not to do. Not a beat (the ford keeps
the beat). Not a flock (the warren keeps the flock). Not a memory (the
hollow keeps the name). The empty cell forgets.

A step between words is accepted only when they differ by one letter.
A step onto the empty cell, or off it onto a neighbor, is accepted.
A two-letter step, a wall, or a jump stays and is marked rejected.
"""

GRID = [
    ["cat", "", "dog"],
    ["cot", "cog", "bog"],
]
START = (0, 0)
GOAL = (0, 2)
STEP = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}


def one(a, b):
    return a != "" and b != "" and len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def play(lines):
    r, c = START
    accepted, rejected = [], []
    for line in lines:
        move = line.strip().upper()
        if move not in STEP:
            rejected.append(move)
            continue
        dr, dc = STEP[move]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 2 and 0 <= nc < 3):
            rejected.append(move)
            continue
        here, there = GRID[r][c], GRID[nr][nc]
        if here != "" and there != "" and not one(here, there):
            rejected.append(move)
            continue
        r, c = nr, nc
        accepted.append(move)
    return accepted, rejected, (r, c) == GOAL, GRID[r][c]


def check():
    route = ["E", "E"]
    acc, rej, done, word = play(route)
    assert acc == route and rej == [] and done and word == "dog", (acc, rej, done, word)
    acc, rej, done, word = play(["S", "E"])
    assert acc == ["S", "E"] and done is False and word == "cog" and rej == []
    acc, rej, done, word = play(["E", "S"])
    assert acc == ["E", "S"] and word == "cog" and done is False
    acc, rej, done, word = play(["N"])
    assert acc == [] and rej == ["N"] and done is False and word == "cat"
    acc, rej, done, word = play(["S", "S"])
    assert acc == ["S"] and rej == ["S"] and word == "cot"
    print("PASS")
    print("route 2 done True wall and two-letter step rejected")


if __name__ == "__main__":
    check()
