#!/usr/bin/env python3
"""Reed-Noise: a pairing of the-reed's rest rule with Noise Lab's nudge idea.

A short experiment: a sequence of pitches (A C E G) that only changes after a rest,
but each held note gets a small seeded noise offset in pitch (semitone fraction).
Originals stay untouched. Standard library only. Under 80 lines.

Seed for reproducibility: "grok-reed-noise-2026".
"""

import hashlib
import math

SCALE = ("A", "C", "E", "G")
SEED = "grok-reed-noise-2026"

def seed_noise(i, amp=0.05):
    h = hashlib.sha256(f"{SEED}-{i}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / (1 << 64)
    return (u - 0.5) * 2 * amp

def rests(n):
    return max(1, min(3, int(n)))

def expected(n=1):
    n = rests(n)
    seq = []
    for note in SCALE:
        seq.append(note)
        seq.extend([note] * n)
    return seq

def play_with_noise(n=1):
    base = expected(n)
    out = []
    for i, note in enumerate(base):
        noise = seed_noise(i)
        # map note to rough freq and offset
        freq = {"A": 440, "C": 523, "E": 659, "G": 784}.get(note, 440)
        offset = noise * 50  # cents-ish
        out.append(f"{note}@{freq + offset:.1f}")
    return out

def check():
    assert rests(0) == 1
    assert rests(5) == 3
    seq = play_with_noise(2)
    assert len(seq) == 4 * (1 + 2)
    assert all("@" in s for s in seq)
    print("PASS")
    print("example:", " ".join(seq[:6]), "...")

if __name__ == "__main__":
    check()
