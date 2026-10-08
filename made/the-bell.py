"""The bell: three rings, only on the beat.

Invitation seed grok-0106-bell, index 0: the-exception.md with period.md.
A ring is the exception. The period is when it is allowed.
"""


def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def on_beat(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines, bell, step = [], 0, 0
    while bell < 3:
        if on_beat(step, n):
            lines.append("ring %s" % bell)
            bell += 1
        else:
            lines.append("rest")
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    bell = 0
    accepted, rejected = [], []
    for i, line in enumerate(lines):
        move = line.strip().lower()
        ok = bell < 3 and (
            move == "rest" or (move == "ring %s" % bell and on_beat(i, n))
        )
        if not ok:
            rejected.append(move)
            continue
        accepted.append(move)
        if move.startswith("ring"):
            bell += 1
    return accepted, rejected, bell == 3


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    route_done = done
    acc, rej, done = play(["ring 1"], 2)
    assert acc == [] and rej == ["ring 1"] and not done
    acc, rej, done = play(["ring 0", "ring 1"], 2)
    assert acc == ["ring 0"] and rej == ["ring 1"] and not done
    assert expected(9) == expected(3)
    assert period(0) == 1
    print("PASS")
    print("period 2 route", len(ex), "done", route_done, "off-beat ring rejected")


if __name__ == "__main__":
    check()
