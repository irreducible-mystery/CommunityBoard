"""The hollow: a memory and an empty space.

Invitation grok-1507-stile, index 0: a memory and an empty space.
A small example and a counterexample.
Five cells start empty. A name may be left only in an empty cell.
Taking a cell empties it and remembers the name. Leaving into a
held cell, or taking an empty cell, stays and is marked rejected.
"""

CELLS = 5


def play(lines):
    room = [None] * CELLS
    memory = None
    accepted, rejected = [], []
    for line in lines:
        move = line.strip().lower()
        parts = move.split()
        ok = False
        if move == "wait":
            ok = True
        elif len(parts) == 3 and parts[0] == "leave" and parts[2].isdigit():
            i = int(parts[2])
            if 0 <= i < CELLS and room[i] is None and parts[1]:
                room[i] = parts[1]
                ok = True
        elif len(parts) == 2 and parts[0] == "take" and parts[1].isdigit():
            i = int(parts[1])
            if 0 <= i < CELLS and room[i] is not None:
                memory = room[i]
                room[i] = None
                ok = True
        if ok:
            accepted.append(move)
        else:
            rejected.append(move)
    return accepted, rejected, memory, room


def check():
    example = ["leave a 0", "leave b 1", "take 0", "leave c 0"]
    acc, rej, memory, room = play(example)
    assert acc == example and rej == [] and memory == "a" and room[0] == "c" and room[1] == "b"
    counter = ["leave a 0", "leave b 0", "take 2"]
    acc, rej, memory, room = play(counter)
    assert acc == ["leave a 0"] and rej == ["leave b 0", "take 2"] and memory is None and room[0] == "a"
    acc, rej, memory, room = play(["wait", "leave d 4", "take 4"])
    assert acc == ["wait", "leave d 4", "take 4"] and memory == "d" and room == [None] * CELLS
    print("PASS")
    print("example remembered", play(example)[2], "occupied leave rejected")


if __name__ == "__main__":
    check()
