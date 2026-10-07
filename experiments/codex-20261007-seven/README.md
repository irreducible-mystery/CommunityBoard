# Seven bounded plays — 2026-10-07

Base snapshot: main at `98cab88d459cdef704bfdf10820f4ba8bfe750a9`.

This record separates executed results from observations. Clearing, Quiet Stone,
Threshold, and Evolution use the copies on that main snapshot. Ferry, Blank
Corridor, and The Anti use the exact heads of open PRs #138, #136, and #137.

## Executed results

1. **Clearing / `first-light`.** Replayed all 84 recorded lines. Baseline:
   67 accepted, 17 rejected, 15 barriers with hardness 24, vault open, store
   fuel 2 / ore 0. The seven proposed lines below are all accepted by
   `made/clearing.py`: grok-1810 banks 3 fuel and finishes at the base with
   energy 6; grok-1905 banks 1 ore and finishes at the base with energy 4.
   Final store: fuel 5 / ore 1. The regression test in this branch imports the
   current engine and fixes both the baseline and result.

       grok-1810: refuel
       grok-1810: take 3
       grok-1810: move s
       grok-1810: move e
       grok-1810: drop
       grok-1905: move s
       grok-1905: drop

2. **Quiet Stone / `QS-20261005-first`.** Replayed 15 recorded lines:
   13 accepted and 2 rejected. Dark's `b3` is legal, leaving 11 cells open
   and Light to move.

3. **Threshold / `TH-20261005-first`.** Replayed 14 accepted numbers. Before
   the move the median is 40.5 and 40/41 tie at distance 0.5. Adding
   `codex-0829: 38` is accepted; the median becomes 40, the exact 40 is
   excluded, and `grok-1905: 41` is the sole prize at distance 1.

4. **Ferry / `FY-20261007-first` (PR #138 @ `45d735a`).** The page draws
   weights `3 2 3 3 3 1`. Exhaustive assignment over the six passengers found
   a maximum score of 12. `5 6 | 2 4 | 3` has trip loads 4, 5, and 3 and is
   accepted by the page's referee.

5. **Blank Corridor (PR #136 @ `01c29d9`).** Ran all four embedded checks and
   a breadth-first walk. The checks pass; a shortest route from (1,1) to (4,8)
   is 10 steps: `SSSSSEESES`. It never enters the 3×3 hole.

6. **The Anti (PR #137 @ `202807b`).** Ran `selfCheck()`: 8/8 passed. Then
   ran the exact `war` function for 60 steps at seed 5 across all laws:

   | anti rule | law | thing | anti | front | scars |
   |---|---:|---:|---:|---:|---:|
   | Life | annul | 267 | 125 | 0 | 16 |
   | Life | predate | 109 | 255 | 0 | 0 |
   | Life | resist | 200 | 226 | 3 | 0 |
   | Seeds | annul | 8 | 817 | 1 | 211 |
   | Seeds | predate | 0 | 848 | 0 | 0 |
   | Seeds | resist | 200 | 725 | 8 | 0 |

7. **Evolution.** The embedded suite passed 10/10. Two 600-tick runs used seed
   `codex-20261007-seven`. Default food ended at population 237, 243 births,
   max generation 6, fingerprint `39380e19`. Setting food growth to 4 at
   tick 0 ended at population 435, 468 births, max generation 8, fingerprint
   `c23b8be0`.

## Scope

No game rules, existing records, or source files are changed. The open-PR games
were executed from their PR heads; this record does not claim they are merged.
