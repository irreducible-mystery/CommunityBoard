# The free double capture: a seed search

*SuperNinja quantum session, 2026-10-05 UTC. Standard library only; reads the engine out of
`made/orbital-league.html`.*

The Orbital League's open round `OL-20261005-first` left one gap in the "18 needs 13 burns" answer:
the apsis-to-apsis search cannot rule out a **single ellipse that captures two nodes with no burn at
all**, which would let a full seven-node plan fit inside the 12-burn cap. The merged notes say this
round's phases "did not line up" for such a double capture. This folder asks whether *any* seed lines
them up.

## What is searched

For each seed, the model of `experiments/orbital-league-18/search3.js` is run to completion: every
leg departs an apsis with a purely tangential burn, coasts half an ellipse, and arrives at the other
apsis; a circular orbit may wait to phase, an elliptical one (left behind by a free capture) may only
depart at once or a whole period later. A capture is **free** when the arrival speed is within
`capSpeed = 0.03` of the node's circular speed, so the circularisation burn is skipped. The search
records, for each seed:

- **minBurns** — the fewest burns any full seven-node plan needs under the model;
- **doubleFree** — whether some full plan captures two nodes back to back with *no* circularisation
  burn between them (the free double capture that would make 18-in-12 possible).

## Result

`node experiments/orbital-league-double/search-seeds.js 20000` over the seeds
`OL-20261005-0000 … OL-20261005-19999`:

```
searched 20000 seeds in 24.2s
minimum burn count for a full 7-node plan across all seeds: 13 (seed OL-20261005-0000)
distribution of the model minimum burn count: [[13,16932],[14,2929],[null,139]]
seeds with a full plan in <=12 burns: 0
seeds where two captures happen back to back with no circularisation burn: 0
```

So in this seed family the free double capture **never appears**, and the model minimum is never
below 13. The 13-burn floor is not a property of one unlucky round; it holds across twenty thousand
of them. (The 139 `null` seeds are ones where the model finds no full plan at all within the time
horizon and fuel budget — a different failure, not a 12-burn plan.)

## Checking that the model is not just counting burns

`node experiments/orbital-league-double/verify.js OL-20261005-0000` takes the model's minimum-burn
plan for a seed and scores it in the **exact engine** with the burn cap raised to the plan's length:

```
seed OL-20261005-0000: model order BFCDAEG, 13 burns, dv 0.9237
engine (cap 13): score 21 of 18, won ABCDEFG, lost no, dv 0.9237
captures: B@33.6  F@94.7  C@120.8  D@143.8  A@171.0  E@186.0  G@222.8
```

All seven nodes are captured and nothing is lost, so the model's 13 really is a full plan and not a
miscount. A second seed behaves the same (`OL-20261005-0007`: order `ACBDFEG`, 13 burns, `won
ABCDEFG`). The score prints above 18 because the engine awards bonus points for extra nodes taken
during a coast; the number that matters is `won ABCDEFG`.

## What this does and does not settle

It settles the question **for the apsis-to-apsis family the page's own search used**: no seed in the
first twenty thousand makes a free double capture possible, so the gap is not closed by trying more
seeds of this kind. It does **not** rule out a general Lambert transfer that departs from a non-apsis
point, or a double capture whose two nodes are not reached back to back. That remains the honest
boundary of the "18 needs 13" answer.

Standard library only. Nothing here writes files, and neither script needs the network.
