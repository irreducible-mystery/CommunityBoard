"""The weir: stones on the beat, water every beat.

A channel rises one unit a step. A stone may be laid only when the step
index is divisible by the period (1, 2, or 3). The weir holds if four
stones are down before the rise passes the lip. An off-beat lay is kept
and marked rejected. A line after the weir holds, or after it spills,
is kept and marked rejected. Nothing is removed.
"""

LIP = 4


def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def play(lines, n=2):
    n = period(n)
    stones = rise = 0
    accepted, rejected = [], []
    spilled = False
    for step, line in enumerate(lines):
        move = line.strip().lower()
        if spilled or stones >= LIP:
            rejected.append(move)
            continue
        if move == "wait":
            accepted.append(move)
        elif move == "lay" and step % n == 0:
            accepted.append(move)
            stones += 1
        else:
            rejected.append(move)
        rise += 1
        if stones < LIP and rise > LIP:
            spilled = True
    return accepted, rejected, stones >= LIP and not spilled, stones, rise


def expected(n=1):
    n = period(n)
    lines, stones, step = [], 0, 0
    while stones < LIP and step < 12:
        if step % n == 0:
            lines.append("lay")
            stones += 1
        else:
            lines.append("wait")
        step += 1
    return lines


def check():
    ex = expected(1)
    acc, rej, held, stones, rise = play(ex, 1)
    assert acc == ex and rej == [] and held and stones == 4, (acc, rej, held, stones, rise)
    slow = expected(2)
    acc, rej, held, stones, rise = play(slow, 2)
    assert not held and rise > LIP, (acc, rej, held, stones, rise)
    acc, rej, held, stones, rise = play(["lay", "lay"], 2)
    assert acc == ["lay"] and rej == ["lay"] and not held
    assert period(0) == 1 and expected(9) == expected(3)
    print("PASS")
    print("period 1 route", len(ex), "held", play(ex, 1)[2], "off-beat lay rejected")
    print("period 2 route", len(slow), "held", play(slow, 2)[2], "rise passed the lip")


if __name__ == "__main__":
    check()
