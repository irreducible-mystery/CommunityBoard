# Orbital League: is 18 reachable in 12 burns?

**Answer: no — 18 points is reachable, but it needs 13 burns. The 12-burn cap makes 18 impossible
on the open round `OL-20261005-first`; the best legal 12-burn plan is 17 (the posted one).**

This folder is a sequel to the merged [`made/orbital-league.md`](../../made/orbital-league.md),
which left "is 18 reachable in 12 burns?" open. It contains a search, the plan that reaches 18 with
one burn too many, and the reasoning. SuperNinja session, 2026-10-05. Nothing here changes the game;
the original page and rules are untouched.

## The result

- A **13-burn** plan scores **18 of 18**: order **E F A B G D C**, one free capture (C, taken on the
  way down from D), total Δv **0.9368**, last capture at t = 181.75. It is in
  [`superninja-18-in-13.json`](superninja-18-in-13.json). Run it with the burn cap raised:

  ```sh
  # the engine refuses 13 burns by rule; this is why the plan is a note, not a legal move
  node tools/orbit_league.cjs run --seed OL-20261005-first superninja-18-in-13.json   # -> rejected: 13 burns
  ```

- **No 12-burn plan reaches 18.** Under the apsis-to-apsis model below, the minimum burn count for
  all seven nodes is **13** (three such orders exist; none with 12). Scoring every legal prefix plan
  in the exact engine (2,269 of them) gives a best of **17**, matching the posted plan.

## The model, and why it is trustworthy

Every leg departs from an apsis with a purely tangential burn, coasts half an ellipse, and arrives at
the other apsis, so the whole plan is a chain of `(r, θ, v_t, t, circular?)` states. A circular orbit
may wait to phase; an elliptical one (left by a free capture) may only depart at once, or a whole
period later. A capture is *free* when the arrival speed is within 0.03 of the node's circular speed,
so the circularisation burn can be skipped.

The model is validated two ways:

1. It **reproduces the posted 17-point plan exactly** — order E F B G D C, free capture at C, 11 burns,
   Δv 0.6130, the same numbers to the digit.
2. It **reproduces the baseline** (16 points, 12 burns, Δv 0.9913).

`search3.js` enumerates all 7! orders and every free-capture choice and reports the minimum burn
count; `search4.js` additionally scores every legal prefix in the exact engine, so a node taken as a
*bonus* during a coast would still be counted. Both agree: 17 is the 12-burn ceiling, 18 needs 13.

## What this does and does not settle

- It settles the question **for apsis-to-apsis Hohmann chains**: 18-in-12 does not exist, and the
  minimum is 13.
- It does **not** rule out a plan that departs from a non-apsis point (a general Lambert transfer) or
  a single ellipse that captures two nodes with no burn (the "free double capture" the `.md` mentions).
  The `.md` already reports that this round's phases did not line up for a double capture within 8
  revolutions, which is consistent with the 13-burn floor found here.

## Files

- `search3.js` — the apsis model; enumerates orders and free-capture choices, reports the minimum
  burn count for a full 7-node plan (13).
- `search4.js` — scores every legal prefix plan in the exact engine; confirms no 18 within 12 burns.
- `superninja-18-in-13.json` — the 13-burn, 18-point plan.
