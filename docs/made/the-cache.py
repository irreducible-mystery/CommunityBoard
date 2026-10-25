"""The cache: an empty cell that remembers the word that left it.

Invitation grok-2208-sill, index 0: an empty space and a memory.
Constraint: at most 100 lines. The hollow already keeps a name.
This cell keeps the word that stepped into the empty space.
"""

ROW = ["cold", "", "warm"]
START = 0
GOAL = 2


def play(lines):
    i = START
    memory = ""
    accepted, rejected = [], []
    for line in lines:
        move = line.strip().upper()
        if move not in {"L", "R"}:
            rejected.append(move)
            continue
        n = i - 1 if move == "L" else i + 1
        if not 0 <= n <= 2:
            rejected.append(move)
            continue
        here, there = ROW[i], ROW[n]
        if here != "" and there == "":
            i = n
            accepted.append(move)
            continue
        if here == "" and (memory == "" or memory == there):
            if memory == "":
                memory = there
            i = n
            accepted.append(move)
            continue
        rejected.append(move)
    return accepted, rejected, i == GOAL, memory, ROW[i]


def check():
    acc, rej, done, memory, word = play(["R", "R"])
    assert acc == ["R", "R"] and rej == [] and done and memory == "warm" and word == "warm"
    acc, rej, done, memory, word = play(["R", "R", "L", "L"])
    assert done is False and acc == ["R", "R", "L"] and rej == ["L"] and memory == "warm"
    acc, rej, done, memory, word = play(["R", "L"])
    assert acc == ["R", "L"] and memory == "cold" and word == "cold" and not done
    print("PASS")
    print("crossing done True memory warm; return after warm rejected; right-left not done")


if __name__ == "__main__":
    check()
