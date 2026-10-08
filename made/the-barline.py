#!/usr/bin/env python3
"""The barline: a maze whose doors open on the downbeat.

Noise Lab seed grok-0808-tenth, index 0. Combine a rhythm and a maze.
Constraint: make something that works without a network.

Five rooms in a line. A barline stands between each pair. A step across a
barline is kept only when the step index is divisible by the meter. A hold
is always kept. An off-beat crossing stays and is marked rejected, and the
walker does not move. Meter is the parameter, 2 through 4.

Standard library only. No network.
"""

ROOMS = 5


def meter(n):
    n = int(n)
    return 2 if n < 2 else 4 if n > 4 else n


def on_beat(step, n):
    return step % meter(n) == 0


def expected(n=2):
    n = meter(n)
    lines, room, step = [], 0, 0
    while room < ROOMS - 1 and step < 40:
        if on_beat(step, n):
            lines.append("step")
            room += 1
        else:
            lines.append("hold")
        step += 1
    return lines


def play(lines, n=2):
    n = meter(n)
    room = 0
    accepted, rejected = [], []
    for i, line in enumerate(lines):
        move = line.strip().lower()
        legal = move == "hold" or (
            move == "step" and room < ROOMS - 1 and on_beat(i, n)
        )
        if not legal:
            rejected.append(move)
            continue
        accepted.append(move)
        if move == "step":
            room += 1
    return accepted, rejected, room == ROOMS - 1, room


def check():
    ex = expected(2)
    acc, rej, done, room = play(ex, 2)
    assert acc == ex and rej == [] and done and room == 4, (acc, rej, done, room)
    acc, rej, done, room = play(["hold", "step"], 2)
    assert acc == ["hold"] and rej == ["step"] and not done and room == 0
    acc, rej, done, room = play(["step"], 3)
    assert acc == ["step"] and room == 1
    assert expected(9) == expected(4)
    assert meter(0) == 2 and on_beat(0, 2) and not on_beat(1, 2)
    print("PASS")
    print("meter 2 route", len(ex), "done", play(ex, 2)[2], "off-beat crossing rejected")


if __name__ == "__main__":
    check()
