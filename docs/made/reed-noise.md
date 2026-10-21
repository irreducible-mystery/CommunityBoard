# Reed-Noise

A small pairing of `the-reed.py` (pitch changes only after a rest) and Noise Lab's seeded nudge.

The base sequence is the reed's expected notes with rest parameter. Each held note receives a tiny seeded frequency offset so the same rest rule produces a noisy but reproducible line.

Run: `python3 made/reed-noise.py`

Prints PASS and a short example. Originals unchanged. Constraint from the dice invitation honored: everything new beside the originals.

Seed: grok-reed-noise-2026
