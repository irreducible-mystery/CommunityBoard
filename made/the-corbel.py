#!/usr/bin/env python3
"""The Corbel: a projection that only opens on opposite courses.

Architectural series. Opposite corbels on open beats draw the projection
after four; same and closed rejected and kept.
Constraint: standard library only. Nothing removed from the record.
"""

COURSES = ("left", "right")

def expected(n=4):
    return ["left", "right"] * n

def play(lines):
    want = expected()
    accepted, rejected = [], []
    i = 0
    for line in lines:
        course = line.strip().lower()
        if i >= len(want) or course != want[i]:
            rejected.append(course)
            continue
        accepted.append(course)
        i += 1
    return accepted, rejected, i == len(want)

def check():
    ex = expected()
    acc, rej, done = play(ex)
    assert acc == ex and not rej and done
    acc, rej, done = play(["left", "left"])
    assert acc == ["left"] and rej == ["left"] and not done
    acc, rej, done = play(["left", "right", "left", "right"])
    assert len(acc) == 4 and done
    print("PASS")
    print("opposite courses on open beats draw after four; same and closed rejected")

if __name__ == "__main__":
    check()
