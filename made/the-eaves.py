"""The eaves: four bays under a roof. A step is accepted only off the drip.

The drip falls on steps where step % period == 0. On those steps only a hold
is kept. A step into the drip, or past the last bay, stays and is marked
rejected. Period is the parameter, 2 through 4. Standard library only.
"""

BAYS = 4


def period(n):
    n = int(n)
    return 2 if n < 2 else 4 if n > 4 else n


def on_drip(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines, bay, step = [], 0, 0
    while bay < BAYS - 1 and step < 40:
        if on_drip(step, n):
            lines.append("hold")
        else:
            lines.append("step")
            bay += 1
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    bay = 0
    accepted, rejected = [], []
    for i, line in enumerate(lines):
        move = line.strip().lower()
        legal = move == "hold" or (
            move == "step" and bay < BAYS - 1 and not on_drip(i, n)
        )
        if not legal:
            rejected.append(move)
            continue
        accepted.append(move)
        if move == "step":
            bay += 1
    return accepted, rejected, bay == BAYS - 1


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["step"], 2)
    assert acc == [] and rej == ["step"] and not done
    acc, rej, done = play(["hold", "hold"], 2)
    assert acc == ["hold", "hold"] and rej == [] and not done
    assert expected(9) == expected(4)
    assert period(0) == 2
    assert on_drip(0, 2) and not on_drip(1, 2)
    print("PASS")
    print("period 2 route", len(ex), "done", done, "drip step rejected")


if __name__ == "__main__":
    check()
