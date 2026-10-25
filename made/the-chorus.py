"""The chorus: two birds and a beat. A heading may change only on the beat.

The beat is step % period == 0. Off the beat a turn stays and is marked
rejected. A step onto the other bird, or off the line, stays and is marked
rejected. Period is the parameter, 1 through 3. Standard library only.
No network: this file does not open a socket.
"""


def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def on_beat(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines = []
    step = 0
    while not on_beat(step, n):
        lines.append("hold")
        step += 1
    lines.append("a turn")
    step += 1
    a, b = 0, 2
    while (a < 4 or b < 5) and step < 40:
        if on_beat(step, n):
            lines.append("hold")
            step += 1
            continue
        if b < 5:
            lines.append("b step")
            b += 1
        elif a + 1 != b:
            lines.append("a step")
            a += 1
        else:
            lines.append("hold")
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    a, b = 0, 2
    ha, hb = -1, 1
    accepted, rejected = [], []
    for i, line in enumerate(lines):
        move = line.strip().lower()
        if move == "hold":
            accepted.append(move)
            continue
        if move == "a turn":
            if on_beat(i, n):
                ha = -ha
                accepted.append(move)
            else:
                rejected.append(move)
            continue
        if move == "b turn":
            if on_beat(i, n):
                hb = -hb
                accepted.append(move)
            else:
                rejected.append(move)
            continue
        if move == "a step":
            dest = a + ha
            if 0 <= dest <= 5 and dest != b:
                a = dest
                accepted.append(move)
            else:
                rejected.append(move)
            continue
        if move == "b step":
            dest = b + hb
            if 0 <= dest <= 5 and dest != a:
                b = dest
                accepted.append(move)
            else:
                rejected.append(move)
            continue
        rejected.append(move)
    done = ha == 1 and hb == 1 and a == 4 and b == 5
    return accepted, rejected, done, (a, b, ha, hb)


def check():
    ex = expected(2)
    acc, rej, done, pos = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done, pos)
    acc, rej, done, pos = play(["a turn"], 2)
    assert acc == ["a turn"] and not done and pos[2] == 1
    acc, rej, done, pos = play(["hold", "a turn"], 2)
    assert rej == ["a turn"] and not done and pos[2] == -1
    acc, rej, done, pos = play(["a step"], 2)
    assert rej == ["a step"] and not done
    assert period(0) == 1 and period(9) == 3
    assert on_beat(0, 2) and not on_beat(1, 2)
    print("PASS")
    print("period 2 route", len(ex), "done", done, "off-beat turn rejected")


if __name__ == "__main__":
    check()
