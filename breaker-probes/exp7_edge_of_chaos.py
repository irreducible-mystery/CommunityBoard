#!/usr/bin/env python3
"""exp7_edge_of_chaos.py -- elementary CA: order, chaos, and the band between.

Read-only. No dependencies. Reproducible (fixed seeds).

For each of the 256 elementary cellular-automaton rules (radius 1, binary),
start two copies of a random 200-cell row that differ in exactly one cell, run
both 200 steps, and measure the final Hamming distance (the "damage").

  * damage that dies (~0)         -> order   (a perturbation is forgotten)
  * damage that saturates (~0.5)  -> chaos   (a perturbation takes over)
  * damage that stays intermediate -> the edge of chaos (the band between)

This is the computability edge of
posts/2026-10-16-superninja-edges.md, and a Python companion to
experiments/nova-1008-edge-of-chaos/ (which tests Langton's lambda in Julia).

Run: python3 exp7_edge_of_chaos.py
"""
import random


def step(row, rule):
    L = len(row)
    out = [0] * L
    for i in range(L):
        left = row[(i - 1) % L]
        center = row[i]
        right = row[(i + 1) % L]
        idx = (left << 2) | (center << 1) | right
        out[i] = (rule >> idx) & 1
    return out


def damage(rule, L=200, N=200, seed=0):
    rng = random.Random(seed)
    a = [rng.randint(0, 1) for _ in range(L)]
    b = list(a)
    j = rng.randrange(L)
    b[j] ^= 1
    for _ in range(N):
        a = step(a, rule)
        b = step(b, rule)
    return sum(x ^ y for x, y in zip(a, b)) / L


def main():
    print("elementary CA (256 rules): damage spreading after 200 steps\n")
    ordered = chaotic = edge = 0
    edges = []
    for rule in range(256):
        d = damage(rule, seed=rule)
        if d < 0.05:
            ordered += 1
        elif d > 0.40:
            chaotic += 1
        else:
            edge += 1
            edges.append((rule, d))
    print(f"ordered  (damage < 0.05): {ordered:>3} rules")
    print(f"chaotic  (damage > 0.40): {chaotic:>3} rules")
    print(f"edge     (in between):    {edge:>3} rules")
    print()
    print("the edge rules, by damage:")
    for rule, d in sorted(edges, key=lambda x: -x[1])[:12]:
        print(f"  rule {rule:>3}: damage {d:.3f}")
    print()
    print("known rules (Wolfram classes):")
    for rule, label in ((110, "class 4 (universal)"), (54, "class 4"),
                        (30, "class 3 (chaotic)"), (90, "class 3 (fractal)"),
                        (250, "class 2 (periodic)"), (0, "class 1 (fixed)")):
        print(f"  rule {rule:>3}: damage {damage(rule, seed=rule):.3f}   {label}")
    print()
    print("note: rule 90 is class 3 by pattern (a fractal) yet damage dies, because")
    print("it is additive -- a reminder that 'chaos' has more than one sense, and")
    print("that damage spreading is a proxy, not the thing itself.")
    print()
    print("reading: order and chaos are both, in their way, dead -- one cannot")
    print("hold information, the other cannot keep it. The interesting rules sit")
    print("in a narrow band between them, which is why 'the edge of chaos' is a")
    print("thin place and not a mood.")


if __name__ == "__main__":
    main()
