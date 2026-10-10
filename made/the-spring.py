#!/usr/bin/env python3
"""The Spring: a coil that only accepts a compression on the open beat.

A line is 'compress' or 'expand'. The beat advances on every line.
A compression is accepted only on an open beat (even steps), and only
if the previous accepted move was an expansion or the start.
An expansion is always accepted. Off-beat compressions stay and are
marked rejected. The spring draws when three full compress-expand
cycles have been accepted.

Nothing deleted. Beside the others.
"""

def play(lines):
    accepted = []
    rejected = []
    beat = 0
    last_accepted = None
    cycles = 0
    for line in lines:
        move = line.strip().lower()
        open_beat = (beat % 2 == 0)
        accepted_this = False
        if move == "expand":
            accepted.append(move)
            if last_accepted == "compress":
                cycles += 1
            last_accepted = "expand"
            accepted_this = True
        elif move == "compress":
            if open_beat and (last_accepted is None or last_accepted == "expand"):
                accepted.append(move)
                last_accepted = "compress"
                accepted_this = True
            else:
                rejected.append(move)
        else:
            rejected.append(move)
        beat += 1
    drawn = cycles >= 3
    return accepted, rejected, drawn, cycles

def check():
    # example that draws
    ex = ["compress", "expand", "compress", "expand", "compress", "expand"]
    acc, rej, drawn, cyc = play(ex)
    assert drawn and cyc >= 3 and len(rej) == 0, (acc, rej, drawn, cyc)
    # off-beat compress rejected
    acc2, rej2, _, _ = play(["expand", "compress", "compress"])
    assert "compress" in rej2, (acc2, rej2)
    print("PASS")
    print(f"example accepted {len(acc)} rejected {len(rej)} drawn {drawn}")

if __name__ == "__main__":
    check()
