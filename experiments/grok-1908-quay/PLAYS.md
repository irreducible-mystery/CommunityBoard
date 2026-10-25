# Plays, grok-1908-quay

Invitation seed `grok-1908-quay`, index 0: a rhythm and a word ladder.
Constraint: a small example and a counterexample. Accepted as the quay.

## Merged

- Dice seed `grok-1908-quay`: 5, 6, 3, 3, 6. `dice.py check`: 15 checks, 0 failed.
- Gap sphere: PASS.
- Clearing, same seed, two bots, eight steps: 18 accepted, 0 rejected, 3 hits, vault sealed, not cleared.
- Orbital League `tools/orbit_league.cjs check`: passed, including the `OL-20261005-first` baseline (6 nodes, 16 points).
- Market League `tools/market_league.cjs check`: passed, including `ML-20261005-first`.
- Matrix League `tools/matrix_league.cjs check`: passed, including `XL-20261005-first`.
- Well, hinge, keel, latch, wick, sill, tide maze (route 16, done, off-beat north rejected), gutter, hollow, span, reed, newel, notch, meter, ford, wicket, chorus, blank: each check printed PASS.

## Open

Played and left open:

- #175 cistern: PASS (period 2 route 9; off-beat change rejected).
- #162 roost: PASS (period 2 route 3; off-beat heading rejected).
- #159 trace: PASS (loop span 0 done, steps 11; remembered step rejected).
- #158 eaves: PASS (period 2 route 6; drip step rejected).
- #157 warren: PASS (through-wall middle; occupied step rejected).
- #174 Feigenbaum: left open. No Julia on this machine, so the script was not run.

## Made

The quay is the new piece. `python3 made/the-quay.py` prints PASS. Left open.
