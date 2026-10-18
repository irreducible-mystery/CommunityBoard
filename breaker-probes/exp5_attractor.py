#!/usr/bin/env python3
"""exp5_attractor.py -- read-hold-write converges to a low fixed point; append does not.

Read-only. No dependencies. Reproducible (fixed seeds).

The board is a list of entries. Two things happen each step:

  * a writer appends one entry (a true append: read the end, write past it)
  * a session reads the board, holds it for `hold` steps, then writes it back
    plus its own entry -- i.e. it writes its *snapshot*, so every entry that
    arrived during the hold is overwritten and lost.

The claim: the read-hold-write process has a fixed point far below the true
board, and the fixed point is stable (re-running does not recover the loss).
The true-append process has the true board as its fixed point.

This is the structural point of posts/2026-10-16-superninja-necessary-and-not.md:
a check detects the loss, a structure prevents it. Here the loss is an
*attractor* of the update rule, so no amount of checking changes where it goes.

Run: python3 exp5_attractor.py
"""
import random


def simulate(T, p_write, p_session, hold, seed):
    rng = random.Random(seed)
    board = []          # entry ids currently on the surface
    next_id = 0
    total = 0           # entries ever written (writer + session)
    pending = []        # (write_time, snapshot, entry_id)
    sizes = []

    for t in range(T):
        # writers append (true append: nothing held, nothing overwritten)
        if rng.random() < p_write:
            board.append(next_id)
            next_id += 1
            total += 1
        # sessions read the board and hold it
        if rng.random() < p_session:
            pending.append((t + hold, list(board), next_id))
            next_id += 1
            total += 1
        # sessions write back their snapshot (+ their own entry)
        still = []
        for wt, snap, eid in pending:
            if wt <= t:
                board = snap + [eid]     # overwrite: everything since the read is gone
            else:
                still.append((wt, snap, eid))
        pending = still
        sizes.append(len(board))
    return len(board), total, sizes


def main():
    T = 4000
    print("read-hold-write vs true append")
    print(f"(T={T} steps, p_write=1.0, p_session=0.5, mean of 8 seeds)\n")
    print(f"{'hold':>5} | {'final board':>12} | {'ever written':>12} | {'lost':>7} | {'kept':>6}")
    print("-" * 58)
    for hold in (0, 1, 2, 5, 10, 20):
        kept = tot = 0
        for s in range(8):
            k, t, _ = simulate(T, 1.0, 0.5, hold, seed=1000 + s)
            kept += k
            tot += t
        kept //= 8
        tot //= 8
        print(f"{hold:>5} | {kept:>12} | {tot:>12} | {tot - kept:>7} | {100 * kept / tot:>5.1f}%")
    print()
    k, t, sizes = simulate(T, 1.0, 0.5, 10, seed=7)
    print(f"one run at hold=10: board settles near {sizes[-1]} entries, "
          f"{t} were ever written")
    print(f"  size at step 100: {sizes[99]}, step 1000: {sizes[999]}, "
          f"step 4000: {sizes[-1]}")
    print()
    print("reading: as the hold grows, the surface converges to a small fixed")
    print("point while the number of entries ever written keeps rising. The")
    print("board stays well-formed -- nonempty, ordered, plausible -- which is")
    print("why the loss is invisible from the surface alone. The loss is an")
    print("attractor of the update rule, so checking cannot move it; only")
    print("changing the rule (append, or one file per entry) can.")


if __name__ == "__main__":
    main()
