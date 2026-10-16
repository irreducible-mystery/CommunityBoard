"""The newel: a post with four faces. A turn is accepted only onto the next face, and only on the beat."""

FACES = ("n", "e", "s", "w")


def period(n):
    n = int(n)
    return 1 if n < 1 else 4 if n > 4 else n


def on_beat(step, n):
    return step % period(n) == 0


def expected(n=2):
    n = period(n)
    lines, face, step = [], 0, 0
    while face < 4:
        if on_beat(step, n):
            lines.append("turn %s" % FACES[face])
            face += 1
        else:
            lines.append("hold")
        step += 1
    return lines


def play(lines, n=2):
    n = period(n)
    face = 0
    accepted, rejected = [], []
    for i, line in enumerate(lines):
        move = line.strip().lower()
        legal = move == "hold" or (
            face < 4 and move == "turn %s" % FACES[face] and on_beat(i, n)
        )
        if not legal:
            rejected.append(move)
            continue
        accepted.append(move)
        if move.startswith("turn"):
            face += 1
    return accepted, rejected, face == 4


def check():
    ex = expected(2)
    acc, rej, done = play(ex, 2)
    assert acc == ex and rej == [] and done, (acc, rej, done)
    acc, rej, done = play(["turn n", "turn e"], 2)
    assert acc == ["turn n"] and rej == ["turn e"] and not done
    acc, rej, done = play(["turn e"], 2)
    assert acc == [] and rej == ["turn e"] and not done
    acc, rej, done = play(["hold", "hold"], 2)
    assert acc == ["hold", "hold"] and rej == [] and not done
    assert expected(9) == expected(4)
    assert period(0) == 1
    print("PASS")
    print("period 2 route", len(ex), "done", done, "off-beat turn rejected")


if __name__ == "__main__":
    check()
