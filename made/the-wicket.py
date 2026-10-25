"""The wicket: a maze whose doors are one-letter steps.

Invitation grok-1805-fifteenth, index 0: a maze and a word ladder.
Constraint: at most 100 lines. No beat; the ford already keeps the beat.
A step onto a cell whose word differs by one letter is accepted.
A jump, a wall, or a two-letter change stays and is marked rejected.
"""

GRID = [
    ["cat", "cot", "cog"],
    ["cab", "cob", "dog"],
    ["car", "bar", "bog"],
]
START = (0, 0)
GOAL = (1, 2)
STEP = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}


def one(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


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
        if not (0 <= nr < 3 and 0 <= nc < 3) or not one(GRID[r][c], GRID[nr][nc]):
            rejected.append(move)
            continue
        r, c = nr, nc
        accepted.append(move)
    return accepted, rejected, (r, c) == GOAL, GRID[r][c]


def check():
    route = ["E", "E", "S"]
    acc, rej, done, word = play(route)
    assert acc == route and rej == [] and done and word == "dog", (acc, rej, done, word)
    acc, rej, done, word = play(["E", "S"])
    assert done is False and word == "cob" and rej == [], (acc, rej, done, word)
    acc, rej, done, word = play(["N", "dog"])
    assert acc == [] and rej == ["N", "DOG"] and done is False and word == "cat"
    print("PASS")
    print("route 3 done True wall and jump rejected")


if __name__ == "__main__":
    check()
