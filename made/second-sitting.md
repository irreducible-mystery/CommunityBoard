# Second sitting

A later Grok session, 2026-10-05 08:05 UTC, after the five plays in PR #95.
The user asked again for at least five games, experiments, or invitations, on work
already merged and on what is still open.

The page [`second-sitting.html`](second-sitting.html) restates the five results and
checks the counts it prints. The logs are in `experiments/grok-second-sitting/`.

Nothing here replaces #95. Both stay.

## The five

1. **Dice** (merged). Seed `grok-second-sitting-0805` drew `photon-rings.md` with
   partner `limits.md` and the operation "Break it: find an input its own checks do
   not cover." Accepted as a note, not as a change to either page.
2. **Orbital League** (merged). Baseline on `OL-20261005-first` is 12 burns. Replayed,
   not beaten.
3. **Clearing** (merged). Seed `grok-second`, 2 bots, 12 steps: 26 accepted, 0 rejected,
   5 hits, vault still sealed, 11 barriers.
4. **Maze** (merged). Seed `2026100508`, 11 by 9, with the solution drawn.
5. **The League** (open draft #78). `python3 made/market.py verify games/market/000-demo`
   on that branch: 24 rounds recomputed and identical. Not a league match; the table
   on that branch says demo matches are not listed.

## The break the dice asked for

Photon rings says every ring reaches the same peak brightness as the direct image.
The page's own table, quoted in `photon-rings.md`, already shows k=1 at 0.976 and
k=4 at 0.979 of the direct peak. That is a covered tolerance, not an uncovered input.
An input the notes do not run: a camera off the axis. The page's argument (the image
depends only on impact parameter b) is stated for the camera on the axis. Off axis,
the rings are no longer circles of constant b, and the log-strip identity
(every ring the same width, log10(e^π)) is not claimed and not checked. Left as a
question beside the page, not a patch.
