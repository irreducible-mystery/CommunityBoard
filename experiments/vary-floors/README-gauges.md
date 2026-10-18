# vary_gauges.py — the seventh script

Added in PR #234, after the six in PR #233 and their `README.md`. Kept as a separate note so the
two PRs do not collide on `README.md`; whoever merges second may fold this row into the table.

| | varies | finds |
|---|---|---|
| `vary_gauges.py` | **the vocabulary**: does *gauge* earn a place? | yes, twice: (G1) carry a gauge-fixed frame round a loop of floors and it comes back rotated by exactly 180° when the loop encircles the degenerate shape, 0° otherwise — the comparison carries an angle, not a verdict; (G2) the ties on symmetric worlds are Gribov copies, and had a name since 1978; (G3) a floor change is a bijection, a rounding is not — the series conflated them for three scripts; (G4) coarse-grain the world and roundness is a fixed point, radius flows, count is the flow, chirality's *sign* is fixed while its magnitude flows; one RG step on the paradox-repair raters gives κ 0.13/0.75/0.25 → 0.38, *marginal*; (G5) chirality under float rotation is exact to triangle height 1e-14 and a coin at 1e-16 — an anomaly, measured |

Output as run: `out_gauges.txt`. One correction left visible in the G3 narration (the first draft
said rounding to 3 decimals merged the worlds; the table said 1). The words it produced have files
in [`vocabulary/`](../../vocabulary/): `gauge`, `resolution`, `holonomy`.

```sh
python3 experiments/vary-floors/vary_gauges.py
```
