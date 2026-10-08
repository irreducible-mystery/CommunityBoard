"""The lintel: a three-room maze whose doors open on the beat."""

def period(n):
    n = int(n)
    return 1 if n < 1 else 3 if n > 3 else n


def open_door(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines, room, step = [], 0, 0
    while room < 2:
        if open_door(step, n):
            lines.append("step %s" % room)
            room += 1
        else:
            lines.append("wait")
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    room = 0
    accepted, rejected = [], []
    for i, line in enumerate(lines):
        move = line.strip().lower()
        if room >= 2 or not (
            move == "wait" or (move == "step %s" % room and open_door(i, n))
        ):
            rejected.append(move)
            continue
        accepted.append(move)
        if move.startswith("step"):
            room += 1
    return accepted, rejected, room == 2


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["step 0", "step 1"], 2)
    assert acc == ["step 0"] and rej == ["step 1"] and not done
    acc, rej, done = play(["wait", "wait", "wait"], 2)
    assert acc == ["wait", "wait", "wait"] and rej == [] and not done
    assert expected(9) == expected(3)
    assert period(0) == 1
    print("PASS")
    print("period 2 route", len(ex), "done", done, "off-beat step rejected")


if __name__ == "__main__":
    check()
