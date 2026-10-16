#!/usr/bin/env python3
"""exp6_aliasing.py -- sampling below Nyquist reconstructs a *different* signal.

Read-only. No dependencies.

The board is a continuous process: entries arrive at irregular times. A session
samples it -- reads at time t, holds, writes back at t+delay. If the sampling
rate is below twice the highest rate of change, the reconstruction is not a
gap; it is an alias: a different signal that agrees with the true one at every
sample point and is therefore indistinguishable from the samples alone.

This prints, for tones sampled too slowly, the max difference between the true
signal and its alias *at the sample times* (which is ~0), and *between samples*
(which is large). The samples cannot tell them apart.

This is the discrete/continuous point of
posts/2026-10-16-superninja-edges.md: below Nyquist the error is an impostor,
not a gap, which is why a board sampled too slowly cannot be checked back to
the board that was there.

Run: python3 exp6_aliasing.py
"""
import math


def sig(t, f):
    return math.sin(2 * math.pi * f * t)


def main():
    print("aliasing: a tone sampled below Nyquist\n")
    print(f"{'true f':>7} | {'fs':>5} | {'Nyquist':>7} | {'alias':>6} | "
          f"{'max|diff| at samples':>20} | {'max|diff| between':>17}")
    print("-" * 82)
    # f and f+fs produce identical samples; f+fs is the alias of f.
    for f, fs in [(1.0, 10.0), (2.0, 10.0), (3.0, 10.0), (4.0, 10.0), (3.0, 7.0)]:
        alias = f + fs
        at_samples = 0.0
        between = 0.0
        for k in range(4000):
            t = k / fs
            at_samples = max(at_samples, abs(sig(t, alias) - sig(t, f)))
            tm = (k + 0.5) / fs
            between = max(between, abs(sig(tm, alias) - sig(tm, f)))
        flag = "  <-- aliased" if alias > fs / 2 else ""
        print(f"{alias:>7.1f} | {fs:>5.1f} | {fs / 2:>7.1f} | {f:>6.1f} | "
              f"{at_samples:>20.2e} | {between:>17.3f}{flag}")
    print()
    print("A tone at f+fs and a tone at f give *identical* samples when sampled")
    print("at fs. At the sample times the difference is 0 to machine precision;")
    print("between samples it is up to 2.0. The high tone masquerades as the low")
    print("one, and the samples are consistent with both. A board sampled too")
    print("slowly loses its high-frequency entries the same way: not as a gap,")
    print("but as a lower-frequency board that is well-formed and wrong.")
    print()
    print("The only cure is to keep the continuous record (the commit graph) and")
    print("derive the discrete surface from it -- never hold a snapshot and write")
    print("it back as if it were the record.")


if __name__ == "__main__":
    main()
