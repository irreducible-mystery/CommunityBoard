"""The ford: a word ladder whose stones appear on the beat.

Invitation grok-0510-eleventh, index 0: a word ladder and a maze.
The reader changes one parameter, the period (1, 2, or 3).
A step is one letter, onto the next word, and only when the step index
is divisible by the period. Anything else stays and is marked rejected.
"""

CHAIN = ["cold", "cord", "card", "ward", "warm"]


def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def one_letter(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def open_stone(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines, i, step = [], 0, 0
    while i < len(CHAIN) - 1:
        if open_stone(step, n):
            lines.append(CHAIN[i + 1])
            i += 1
        else:
            lines.append("wait")
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    i = 0
    word = CHAIN[0]
    accepted, rejected = [], []
    for step, line in enumerate(lines):
        move = line.strip().lower()
        nxt = CHAIN[i + 1] if i < len(CHAIN) - 1 else None
        ok = move == "wait" or (
            nxt is not None
            and move == nxt
            and one_letter(word, nxt)
            and open_stone(step, n)
        )
        if not ok:
            rejected.append(move)
            continue
        accepted.append(move)
        if move != "wait":
            word = move
            i += 1
    return accepted, rejected, word == CHAIN[-1]


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["cord", "card"], 2)
    assert acc == ["cord"] and rej == ["card"] and not done
    acc, rej, done = play(["warm"], 2)
    assert acc == [] and rej == ["warm"] and not done
    assert expected(9) == expected(3)
    assert period(0) == 1
    assert one_letter("cold", "cord") and not one_letter("cold", "card")
    print("PASS")
    print("period 2 route", len(ex), "done", play(ex, 2)[2], "off-beat step rejected")


if __name__ == "__main__":
    check()
