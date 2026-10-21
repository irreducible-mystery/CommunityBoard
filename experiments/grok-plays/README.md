# grok-plays

Records from the 2026-10-05 Grok session. Nothing here is a rule change.

- `orbit-grok-early-two.json` — plan for seed `OL-20261005-first`. Scores 4 against the baseline (node G shared); D remains open.
- `clearing-grok-tide.txt` — 82 accepted moves on seed `grok-tide`. Not cleared.
- `maze-20261005.svg` — maze.py seed 20261005, 15×11, solution drawn.

Replay:

```sh
node tools/orbit_league.cjs run --seed OL-20261005-first experiments/grok-plays/orbit-grok-early-two.json
python3 made/clearing.py replay grok-tide experiments/grok-plays/clearing-grok-tide.txt
```
