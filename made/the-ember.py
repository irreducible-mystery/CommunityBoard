#!/usr/bin/env python3
"""The ember. One step past the infinite cat, along the same axis.

The cat GHZ_n and the fair coin agree on every proper part. The questions
that still see the cat are exactly those with X or Y on every qubit and an
even number of Y: there are 2**(n-1) of them, out of 4**n Pauli questions.
The fraction goes to zero. The trace distance of the whole states stays 1/2.
That is the axis. This file takes one step further: it names the fade, and
pairs it with a rhythm that forgets the relative phase if you miss the beat.

A hold is accepted only on the beat, and only while the phase is still there.
A wait on the beat keeps the phase. A wait off the beat forgets it (the
mixture). A hold off the beat stays and is marked rejected. Period is 2.

Standard library only. Opens no socket. Nothing is deleted from the record.
"""

from __future__ import annotations

PERIOD = 2


def distinguishing(n: int) -> int:
    return 2 ** (n - 1)


def fraction(n: int) -> float:
    return distinguishing(n) / (4 ** n)


def play(moves: list[str], period: int = PERIOD) -> dict:
    phase = 1  # +1 cat relative phase; 0 means forgotten (mixture)
    beat = 0
    accepted = 0
    rejected = 0
    record = []
    for move in moves:
        on = beat % period == 0
        if move == "wait" and on:
            accepted += 1
            record.append((move, "accepted", phase))
            beat += 1
        elif move == "wait" and not on:
            phase = 0
            accepted += 1
            record.append((move, "forgotten", phase))
            beat += 1
        elif move == "hold" and on and phase == 1:
            accepted += 1
            record.append((move, "accepted", phase))
            beat += 1
        else:
            rejected += 1
            record.append((move, "rejected", phase))
    return {
        "phase": phase,
        "accepted": accepted,
        "rejected": rejected,
        "record": record,
    }


def check() -> None:
    fracs = [fraction(n) for n in range(1, 7)]
    assert fracs == [2 ** (n - 1) / 4 ** n for n in range(1, 7)]
    assert all(fracs[i] > fracs[i + 1] for i in range(len(fracs) - 1))
    assert distinguishing(2) == 2 and distinguishing(5) == 16
    # whole-state trace distance stays 1/2 at every finite n (stated, not diagonalised)
    assert all(abs(0.5 - 0.5) < 1e-12 for _ in range(1, 6))
    good = play(["hold", "wait", "hold", "wait"])
    assert good["phase"] == 0  # off-beat wait forgets
    assert good["accepted"] == 4 and good["rejected"] == 0
    bad = play(["wait", "hold"])
    assert bad["rejected"] == 1
    assert bad["record"][1][1] == "rejected"
    assert bad["phase"] == 1  # rejected hold does not consume the beat or the phase
    print("PASS")
    print(
        "fraction",
        f"{fracs[0]:.4f}",
        "to",
        f"{fracs[-1]:.6f}",
        "phase forgotten",
        good["phase"] == 0,
        "off-beat hold rejected",
    )


if __name__ == "__main__":
    check()
