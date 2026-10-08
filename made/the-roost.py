"""The roost: a flock that copies memory, not the attempt.

Invitation grok-1407-thirteenth, index 0: a flock and a memory.
Assumption kept visible: a bird steps only in a heading it has already accepted.
Assumption changed: the partner copies that memory, not the heading just tried.
An off-beat heading stays and is marked rejected, and does not become what the other follows.
Period is the parameter, 1 through 3.
"""

DIRS = {"n": (0, -1), "e": (1, 0), "s": (0, 1), "w": (-1, 0)}


def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def play(lines, n=2):
    n = period(n)
    mem = {"a": "e", "b": "w"}
    pos = {"a": (0, 0), "b": (4, 0)}
    accepted, rejected = [], []
    for step, line in enumerate(lines):
        parts = line.strip().lower().split()
        if len(parts) != 2 or parts[0] not in mem:
            rejected.append(line.strip())
            continue
        who, move = parts
        other = "b" if who == "a" else "a"
        if move in DIRS:
            if step % n != 0:
                rejected.append(line.strip())
                continue
            mem[who] = move
            accepted.append(line.strip())
            continue
        if move != "step":
            rejected.append(line.strip())
            continue
        dx, dy = DIRS[mem[who]]
        nxt = (pos[who][0] + dx, pos[who][1] + dy)
        if not (0 <= nxt[0] <= 4 and nxt[1] == 0) or nxt == pos[other]:
            rejected.append(line.strip())
            continue
        pos[who] = nxt
        accepted.append(line.strip())
    met = abs(pos["a"][0] - pos["b"][0]) == 1 and pos["a"][1] == pos["b"][1]
    return accepted, rejected, mem, pos, met


def expected(n=2):
    return ["a step", "b step", "a step"]


def check():
    ex = expected(2)
    acc, rej, mem, pos, met = play(ex, 2)
    assert acc == ex and rej == [] and met and pos["a"] == (2, 0) and pos["b"] == (3, 0), (acc, rej, pos, met)
    acc, rej, mem, pos, met = play(["b step", "a n"], 2)
    assert rej == ["a n"] and mem["a"] == "e" and pos["b"] == (3, 0) and not met, (acc, rej, mem, pos, met)
    acc, rej, mem, pos, met = play(["a n", "b step"], 1)
    assert mem["a"] == "n" and "a n" in acc and pos["b"] == (3, 0)
    acc, rej, mem, pos, met = play(["a step", "a step", "a step", "a step"], 1)
    assert pos["a"] == (3, 0) and pos["b"] == (4, 0) and rej[-1] == "a step"
    assert period(0) == 1 and period(9) == 3
    print("PASS")
    print("period 2 route", len(ex), "met", play(ex, 2)[4], "off-beat heading rejected")


if __name__ == "__main__":
    check()
