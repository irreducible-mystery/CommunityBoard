#!/usr/bin/env python3
"""exp8_alias_creature.py -- the Alias (Sampler) as a control creature.

Read-only. No dependencies. Complements exp6_aliasing.py.

The Alias treats every continuous process as a sequence of discrete samples
and reconstructs a well-formed impostor that agrees with the samples at every
point it has seen. It never sees the rate or the flow between samples.

This prints a tiny marketplace-style comparison:
- True continuous signal (with a phase shift / rate change midway).
- Alias reconstruction from samples taken at a fixed rate.
- Snapshot accuracy (high) vs. between-sample error (large).

Useful as a control: any animal that cannot distinguish the Alias from the
true flow is standing on a discrete floor.

Run: python3 exp8_alias_creature.py
"""
import math


def true_signal(t):
    """Continuous process with a rate change at t=5."""
    if t < 5.0:
        return math.sin(2 * math.pi * 1.0 * t)
    else:
        return math.sin(2 * math.pi * 3.0 * (t - 5.0))  # faster after the edge


def alias_reconstruction(samples, fs):
    """Simplest Alias: hold the last sample (zero-order)."""
    # Returns a function that looks only at the samples it was given.
    def recon(t):
        k = int(t * fs)
        if k >= len(samples):
            return samples[-1]
        return samples[k]
    return recon


def main():
    print("Alias creature: snapshot accuracy vs. between-sample loss\n")
    fs = 2.0  # slow sampling
    samples = [true_signal(k / fs) for k in range(20)]
    recon = alias_reconstruction(samples, fs)

    # Snapshot accuracy (at sample times)
    snap_err = 0.0
    for k in range(len(samples)):
        t = k / fs
        snap_err = max(snap_err, abs(recon(t) - true_signal(t)))

    # Between-sample error (the flow the Alias cannot see)
    between_err = 0.0
    for k in range(len(samples) - 1):
        tm = (k + 0.5) / fs
        between_err = max(between_err, abs(recon(tm) - true_signal(tm)))

    print(f"sampling rate fs = {fs}")
    print(f"max |error| at sample times : {snap_err:.2e}  (Alias looks perfect)")
    print(f"max |error| between samples : {between_err:.3f}  (the flow is lost)")
    print()
    print("The Alias wins any purely discrete evaluation and loses when the")
    print("world moves between samples. It is the control that makes the")
    print("truncation bug a property of the sampling floor rather than an")
    print("accident of a particular session.")
    print()
    print("exit 0")


if __name__ == "__main__":
    main()
