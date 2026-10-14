#!/usr/bin/env python3
"""the-void-memory.py — an empty space that remembers the last few steps.

Combine an empty space and a memory. The space is a line of cells, all empty.
A walker steps left or right. The memory holds the last K positions visited.
A step onto a cell still in the recent memory is rejected (kept and marked).
The parameter is K, the memory length, which a reader can change.

Seed grok-1014-sitting. Standard library only. Nothing deleted.
"""
import sys

def play(k=2, steps=None):
    if steps is None:
        steps = ["r", "r", "l", "r", "l", "l"]
    pos = 0
    memory = []
    accepted = 0
    rejected = 0
    trail = [pos]
    for s in steps:
        next_pos = pos + (1 if s == "r" else -1)
        recent = memory[-k:] if k > 0 else []
        if next_pos in recent:
            rejected += 1
            trail.append(f"rejected-{s}")
            continue
        pos = next_pos
        memory.append(pos)
        accepted += 1
        trail.append(pos)
    return {"k": k, "accepted": accepted, "rejected": rejected, "final": pos, "trail": trail}

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # small example: k=2 rejects the return step
        ex = play(2, ["r", "r", "l"])
        assert ex["rejected"] == 1 and ex["accepted"] == 2, ex
        # counterexample: k=0, no memory, return is accepted
        cx = play(0, ["r", "r", "l"])
        assert cx["rejected"] == 0 and cx["accepted"] == 3, cx
        print("PASS")
        print("example k=2:", ex)
        print("counterexample k=0:", cx)
        return
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print(play(k))

if __name__ == "__main__":
    main()
