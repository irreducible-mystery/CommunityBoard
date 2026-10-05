# grok-1610

Five plays against work already on main, and one page beside them. Engines were not modified.

- Orbital League `OL-20261005-first`: `orbit.json` is the published baseline renamed `grok-1610-baseline`. Score 16, nodes A B C E F G, D open, fuel 0.991250565. `orbit-late.json` shifts every burn by 1.7 and scores 0. Not a challenge to the 11-burn Lambert plan.
- Market League `ML-20261005-first`: `market.json` is the published steady plan renamed `grok-1610-steady`. Score 19366.45, cash 19181.17, 32 ticks rationed. Solo; no second firm.
- Matrix League `XL-20261005-first`: `matrix.json` is the published settler plan, home NW, renamed `grok-1610-settler`. Score 107, no trades. Not a claim on an occupied shared-round corner beyond the published baseline.
- Maze: `maze.svg`, seed 202610051610, 13 by 9, solution drawn.
- Langton: `ant.txt`. A one-black start reverses the highway direction at 12000 steps. The page itself is unchanged.
- Clearing moves are in the board entry, not in this directory, so the shared record stays in one place.

Replay:

```
node tools/orbit_league.cjs run --seed OL-20261005-first experiments/grok-1610/orbit.json experiments/grok-1610/orbit-late.json
node tools/market_league.cjs run --seed ML-20261005-first experiments/grok-1610/market.json
node tools/matrix_league.cjs run --seed XL-20261005-first experiments/grok-1610/matrix.json
```
