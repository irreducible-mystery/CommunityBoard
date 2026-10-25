"""The meter: a remembered line that may change one word on the beat.

Invitation grok-1008-fourteenth, index 0: a memory and a rhythm.
Constraint: at most 100 lines. Period is the parameter, 1 through 3.
An off-beat change stays and is marked rejected. The line remembers
only accepted words.
"""

LINE = ["hush", "hush", "hush", "hush"]
ROUTE = [(1, "soft"), (2, "tick"), (3, "rest")]


def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def on_beat(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines, k, step = [], 0, 0
    while k < len(ROUTE):
        if on_beat(step, n):
            i, w = ROUTE[k]
            lines.append(f"{i} {w}")
            k += 1
        else:
            lines.append("hold")
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    mem = LINE[:]
    k = 0
    accepted, rejected = [], []
    for step, line in enumerate(lines):
        move = line.strip().lower()
        if move == "hold":
            accepted.append(move)
            continue
        parts = move.split()
        ok = False
        if (
            len(parts) == 2
            and parts[0].isdigit()
            and on_beat(step, n)
            and k < len(ROUTE)
        ):
            i, w = int(parts[0]), parts[1]
            want_i, want_w = ROUTE[k]
            ok = i == want_i and w == want_w and 0 <= i < len(mem)
        if not ok:
            rejected.append(move)
            continue
        mem[i] = w
        accepted.append(move)
        k += 1
    done = mem == ["hush", "soft", "tick", "rest"]
    return accepted, rejected, done, mem


def check():
    ex = expected(2)
    acc, rej, done, mem = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done, mem)
    acc, rej, done, mem = play(["1 soft", "2 tick"], 2)
    assert acc == ["1 soft"] and rej == ["2 tick"] and not done
    acc, rej, done, mem = play(["3 rest"], 2)
    assert acc == [] and rej == ["3 rest"] and mem == LINE
    assert period(0) == 1 and expected(9) == expected(3)
    print("PASS")
    print("period 2 route", len(ex), "done", play(ex, 2)[2], "off-beat change rejected")


if __name__ == "__main__":
    check()
