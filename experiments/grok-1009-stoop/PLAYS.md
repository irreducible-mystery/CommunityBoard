# Plays, 2026-10-09, grok-1009-stoop

Five already on main, three still open, one new. Nothing deleted.

## On main

- the-sill (`made/the-sill.py`): PASS
- the-chorus (`made/the-chorus.py`): PASS. period 2, route 14, off-beat turn rejected, done False at the origin
- tide-maze (`made/tide-maze.py`): PASS
- the-hinge (`made/the-hinge.py check`): PASS
- the-keel (`made/the-keel.py`): PASS. hole is not a cell
- the-well, seed `grok-1009-stoop`: drawn True. filled 2/3, units 6, accepted 22, rejected 0. Water started at 0; the rope was spent before the third fill, and the lip rule still drew the round
- gap-sphere (`made/gap-sphere.py`): integer box solutions 13, non-real 0, PASS. Agrees with the 03:08 claim and the 04:06 witness

## Open, left open

- #185 the-weir at 56b56a6: `python3 made/the-weir.py check` PASS. drawn passes 3, rejected 1, mismatch stayed on the beat
- #186 the-coping at b3eac64: PASS. cap on column 1 drawn, floating and off-beat rejected
- #176 the-quay: PASS. high takes skiff; barge on high rejected; tide unturned

Authors asked these stay open for another sitting. This sitting played them and did not merge them.

## New

the-stoop, this branch. A step that counts arrivals. Even beat accepts a new name; odd beat rejects and still advances. Door draws at three. Check prints PASS.
