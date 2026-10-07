#!/usr/bin/env python3
"""The Span: a footbridge that only accepts a plank next to one already laid.

Noise Lab seed grok-2105-span, index 0: an empty space and a ladder.
Constraint: at most 100 lines. Standard library only.

The near bank counts as laid. A line is a plank index. The parameter is
the length, 3 through 6. A plank on a taken index, or with no neighbour
already laid, is kept and marked rejected. The far bank is reached when
every index is laid. Nothing is removed from the record.
"""

def length(n):
    return max(3, min(6, int(n)))

def play(lines, n=4):
    n = length(n)
    laid = set()
    accepted, rejected = [], []
    for raw in lines:
        word = raw.strip()
        if not word.isdigit():
            rejected.append(word)
            continue
        idx = int(word)
        if not (0 <= idx < n) or idx in laid:
            rejected.append(word)
            continue
        if idx != 0 and (idx - 1) not in laid:
            rejected.append(word)
            continue
        laid.add(idx)
        accepted.append(word)
    return accepted, rejected, len(laid) == n, n

def check():
    acc, rej, done, n = play(["0", "1", "2", "3"], 4)
    assert acc == ["0", "1", "2", "3"] and rej == [] and done and n == 4
    acc, rej, done, n = play(["2", "0", "1"], 4)
    assert acc == ["0", "1"] and rej == ["2"] and not done
    acc, rej, done, n = play(["0", "0"], 3)
    assert acc == ["0"] and rej == ["0"] and not done
    assert length(9) == 6 and length(1) == 3
    print("PASS")
    print("span 4 done", done, "gap plank rejected")

if __name__ == "__main__":
    check()
