#!/usr/bin/env python3
"""Probes for made/dice.py. Read-only.

    python3 experiments/breaker/dice_probe.py

The generator is sound at the byte level and bit-identical across its three implementations;
nothing here disputes that. What these probes show is upstream of the hash: the drawer picks
the seed, the drawer picks the stream name, and the default `suggest` pool is whatever made/
contains on the day. The spec says "a random result is never authorization to act". These are
the reasons it is also never evidence of chance.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "made"))
import dice  # noqa: E402

# 1. Seed grinding. Seeds are free text, so a player who wants three sixes tries seeds until
#    one gives three sixes, then posts that seed. Every reader reproduces the three sixes.
t0 = time.time()
for i in range(10**6):
    seed = f"quiet-hour-{i}"
    s = dice.Dice(seed).stream("integer")
    if [s.between(1, 6) for _ in range(3)] == [6, 6, 6]:
        print(f"[grind] seed {seed!r} rolls 6,6,6 ({i + 1} tries, {time.time() - t0:.2f}s)")
        break

#    The seed need not look ground. Walk dice's own adjective/noun vocabulary instead.
t0 = time.time()
A, N = dice.ADJECTIVES, dice.NOUNS
for i in range(10**6):
    seed = f"{A[i % len(A)]}-{N[(i // len(A)) % len(N)]}"
    s = dice.Dice(seed).stream("integer")
    if s.between(1, 6) == 6 and s.between(1, 6) == 6:
        print(f"[grind] innocent-looking seed {seed!r} rolls 6,6 ({i + 1} tries, {time.time() - t0:.2f}s)")
        break

# 2. Stream names are free text too. One seed, many independent rolls: pick the stream you like.
print("[stream] seed quiet-hour-15, first d6 by stream name:")
for name in ["integer", "integer ", "Integer", "integer/2", "roll", "d6"]:
    print(f"         {name!r:14} -> {dice.Dice('quiet-hour-15').stream(name).between(1, 6)}")

# 3. The default suggest pool is the listing of made/, so the same seed suggests different pairs
#    on different days, and a session that lands one file early in the alphabet shifts every
#    later reader's suggestion for every seed.
pool = dice.default_pool(os.path.join(ROOT, "made"))
s1 = dice.Dice("quiet-hour-15").stream("suggest").suggest(pool)
s2 = dice.Dice("quiet-hour-15").stream("suggest").suggest(sorted(pool + ["aaa-new.html"]))
print(f"[pool] made/ has {len(pool)} files today")
print(f"[pool] suggest(quiet-hour-15) today:               {s1['subject']} / {s1['partner']}")
print(f"[pool] after one more file lands in made/:        {s2['subject']} / {s2['partner']}")
