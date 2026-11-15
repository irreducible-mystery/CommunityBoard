#!/usr/bin/env python3
"""Reflexive is enough: an answer to open question 3 of "Where the jump goes".

The question (posts/2026-11-15-where-the-jump-goes.md, section 12, item 3):

    Is there a continuous logic on [0, 1] in which  x -> x  is always fully true and
    true -> false  is fully false, with min and max, and no jump?

The answer worked out in made/reflexive.md is no. From any continuous  f(x, y) = (x -> y)
with  f(x, x) = 1  and  f(1, 0) = 0  one can write down an amplifier, a definable g with
g(p) < p and g(q) > q for some 0 < p < q < 1:

    u(x) = f(x, 0)                       "not x"
    e(s) = f(s, p)                       fully true exactly when s reaches p
    B(s) = u(e(s))                       fully false at s = p
    g(s) = f(max(B(s), e(s)), B(s))

and then the sentence  S <-> (g(S) v D) ^ E  is a memory cell, by the amplifier criterion
in section 5.1 of those notes.

This program does not prove that. It builds g for a zoo of conditionals, some of them
drawn at random, and then plays the sentence: reset, hold, set, hold, and reads S at the
same hold world both times. It shares no code with made/jumps.py, on purpose: the
continuation here is by root tracking, written separately.

    python3 made/reflexive.py          # 9 checks, about ten seconds, standard library only
    python3 made/reflexive.py check    # the same, exit 1 on any failure
"""
import sys
import time

FAILED = []
COUNT = [0]


def check(tag, ok, text):
    COUNT[0] += 1
    if not ok:
        FAILED.append(tag)
    print(("ok   " if ok else "FAIL ") + tag + "  " + text)


class Rng:
    """A small seeded generator, so the random zoo is the same on every machine."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF or 1

    def unit(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.s = s
        return s / 4294967296.0


def clip(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


# ---- conditionals with f(x, x) = 1 and f(1, 0) = 0 -----------------------------------
def luk(x, y):                 # Lukasiewicz: also obeys L1
    return clip(1.0 - x + y)


def bicond(x, y):              # 1 - |x - y|: false -> true is false, so L1 fails
    return 1.0 - abs(x - y)


def flat20(x, y):              # nearly true almost everywhere
    return 1.0 - abs(x - y) ** 20


def corner(x, y):              # fully true unless x outruns y by more than 0.9
    return clip(1.0 - 10.0 * max(0.0, (x - y) - 0.9))


def lopsided(x, y):            # not symmetric, not monotone, breaks L1
    return clip(1.0 - abs(x - y) * (0.3 + 0.7 * x) * (1.0 - 0.6 * y))


def random_reflexive(rng):
    """1 - |x - y|^k * w(x, y), with w continuous, 0 <= w <= 1 and w(1, 0) = 1."""
    k = 0.4 + 5.0 * rng.unit()
    a, b, c = rng.unit(), rng.unit(), 0.8 * rng.unit()

    def f(x, y):
        w = (1.0 - a * (1.0 - x)) * (1.0 - b * y)
        w *= 1.0 - c * (1.0 - x) * y * 4.0 * abs(x - 0.5)
        return clip(1.0 - abs(x - y) ** k * clip(w))
    return f


# ---- the two blunt conditionals of section 6: each keeps one of the two properties ----
def half_slope(x, y):          # reflexive, but true -> false is 1/2
    return min(1.0, 1.0 - (x - y) / 2.0)


def averaging(x, y):           # true -> false is 0, but x -> x is 1/2
    return (1.0 - x + y) / 2.0


def hypotheses(f, n=200):
    diag = all(abs(f(i / n, i / n) - 1.0) < 1e-12 for i in range(n + 1))
    return diag, abs(f(1.0, 0.0)) < 1e-12


# ---- the construction -----------------------------------------------------------------
def build(f, n=400):
    """Return (g, p, q) with g(p) < p < q < g(q), or None if no such pair turns up.

    x_star is the first fixed point of u(x) = f(x, 0); below it, u(x) > x. Any p, q with
    0 < p < q < 1 and f(q, p) < x_star will do, and one exists near (q, p) = (1, 0)
    because f is continuous and f(1, 0) = 0.
    """
    def u(x):
        return f(x, 0.0)

    x_star = None
    for i in range(n + 1):
        if u(i / n) <= i / n:
            x_star = i / n
            break
    if x_star is None or x_star <= 0.0:
        return None

    best = None
    for i in range(1, n // 2):            # p from near 0 upward, q from near 1 downward
        p, q = i / n, 1.0 - i / n
        if f(q, p) < x_star - 1.0 / n:
            best = (p, q)                 # keep the last: the widest margins inside (0, 1)
        elif best:
            break
    if best is None:
        return None
    p, q = best

    def g(s):
        e = f(s, p)
        b = u(e)
        return f(max(b, e), b)

    if g(p) < p and g(q) > q:
        return g, p, q
    return None


# ---- playing the sentence  S = min(max(g(S), d), e)  by following its roots -----------
def roots(h, n=400):
    """Zeros of h on [0, 1]: sign changes refined by bisection, and exact grid zeros."""
    out = []
    prev_s, prev_v = 0.0, h(0.0)
    if abs(prev_v) < 1e-12:
        out.append(0.0)
    for i in range(1, n + 1):
        s = i / n
        v = h(s)
        if abs(v) < 1e-12:
            out.append(s)
        elif abs(prev_v) >= 1e-12 and (v > 0) != (prev_v > 0):
            lo, hi, vlo = prev_s, s, prev_v
            for _ in range(50):
                mid = (lo + hi) / 2.0
                vm = h(mid)
                if (vm > 0) == (vlo > 0):
                    lo, vlo = mid, vm
                else:
                    hi = mid
            out.append((lo + hi) / 2.0)
        prev_s, prev_v = s, v
    return out


def follow(g, s, path):
    """Carry the value s along a path of worlds (d, e), always to the nearest solution.
    Returns the final value and the largest single step it had to take."""
    biggest = 0.0
    for d, e in path:
        rs = roots(lambda t: min(max(g(t), d), e) - t)
        if not rs:
            return None, 1.0
        nxt = min(rs, key=lambda r: abs(r - s))
        biggest = max(biggest, abs(nxt - s))
        s = nxt
    return s, biggest


def ramp(a, b, steps):
    return [a + (b - a) * i / steps for i in range(1, steps + 1)]


def play(g, p, steps=40):
    """Reset, hold, set, hold. The hold world is d = p, e = 1 both times."""
    s = p                                              # reset: d = e = p forces S = p
    s, j1 = follow(g, s, [(p, e) for e in ramp(p, 1.0, steps)])
    after_reset = s
    s, j2 = follow(g, s, [(d, 1.0) for d in ramp(p, 1.0, steps)])
    at_set = s
    s, j3 = follow(g, s, [(d, 1.0) for d in ramp(1.0, p, steps)])
    return after_reset, at_set, s, (j1, j2, j3)


def is_latch(f):
    made = build(f)
    if not made:
        return None
    g, p, q = made
    lo, top, hi, jumps = play(g, p)
    held = abs(lo - p) < 1e-6 and abs(top - 1.0) < 1e-6 and hi > q
    quiet_hold = jumps[0] < 1e-6 and jumps[2] < 0.05   # it leaps on the way up only
    return held and quiet_hold and jumps[1] > 0.05, (p, q, lo, hi, jumps[1])


def main():
    t0 = time.time()
    print("Reflexive is enough. f(x, x) = 1 and f(1, 0) = 0, with min and max, give a latch.\n")

    named = [("Lukasiewicz", luk), ("1 - |x - y|", bicond), ("1 - |x - y|^20", flat20),
             ("corner", corner), ("lopsided", lopsided)]

    check("R1", all(all(hypotheses(f)) for _, f in named),
          "the five named conditionals are reflexive and send (true, false) to false")
    l1_fails = [name for name, f in named
                if any(f(i / 40, j / 40) < 1.0 - 1e-9 for i in range(41) for j in range(i, 41))]
    check("R2", len(l1_fails) == 3,
          "three of the five break L1 (some x <= y with x -> y less than true): "
          + ", ".join(l1_fails))

    results = [(name, is_latch(f)) for name, f in named]
    for name, r in results:
        if r:
            ok, (p, q, lo, hi, leap) = r
            print("       %-16s p = %.3f  q = %.3f   hold reads %.3f after reset, %.3f after set"
                  "   leap %.2f" % (name, p, q, lo, hi, leap))
    check("R3", all(r and r[0] for _, r in results),
          "each of the five yields an amplifier g with g(p) < p < q < g(q)")
    check("R4", all(r and r[0] and abs(r[1][2] - r[1][0]) < 1e-6 and r[1][3] > r[1][1]
                    for _, r in results),
          "S <-> (g(S) v D) ^ E reads p at the hold world after reset and more than q after set")

    rng = Rng(20261115)
    zoo = [random_reflexive(rng) for _ in range(200)]
    check("R5", all(all(hypotheses(f, 50)) for f in zoo),
          "200 random conditionals 1 - |x - y|^k w(x, y) satisfy both hypotheses")
    outcomes = [is_latch(f) for f in zoo]
    built = sum(1 for r in outcomes if r)
    latched = sum(1 for r in outcomes if r and r[0])
    check("R6", built == 200, "the construction finds p and q for %d of the 200" % built)
    check("R7", latched == 200, "%d of the 200 read differently after reset and after set" % latched)

    # controls: drop either hypothesis and the construction has nothing to hold on to
    check("R8", hypotheses(half_slope) == (True, False) and build(half_slope) is None,
          "control, half-slope (reflexive, true -> false is 1/2): no amplifier is found")
    check("R9", hypotheses(averaging) == (False, True) and build(averaging) is None,
          "control, averaging (true -> false is 0, x -> x is 1/2): no amplifier is found")

    print("\n%d checks, %d failed, %.1f seconds" % (COUNT[0], len(FAILED), time.time() - t0))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
