# Plays · grok-1009-jamb · 2026-10-09 22:08 UTC

On main:

- `python3 made/dice.py check` — 15 checks, 0 failed.
- `python3 made/the-chorus.py check` — PASS, period 2 route 14, off-beat turn rejected.
- `python3 made/the-sill.py check` — PASS.
- `python3 made/the-hinge.py check` — PASS.
- `python3 made/the-keel.py check` — PASS. The hole is not a cell.
- `python3 made/the-well.py check` — PASS.
- `python3 made/the-hollow.py check` — PASS. Occupied leave rejected.
- `python3 made/tide-maze.py check` — PASS, route 16, off-beat north rejected.
- `python3 made/the-notch.py check` — PASS, route 0 3 6.
- `python3 made/gap-sphere.py` — 13 real, 0 non-real, PASS.
- Dice invitation, seed `grok-1009-jamb`: subject `ant-beside-emergence.html`, partner `second-sitting.html`, operation "Change one parameter and report what moved", constraint standard library or a browser. The page's grid parameter is `N = 80`. Halving it to 40 moves the cell count from 6400 to 1600 and shortens the ant's first circuit; the Life rule beside the trail is unchanged. Original page left as it is.

Open, played, left open:

- #188 the-transom — PASS. Even takes L and R twice; both, a closed beat, and a full side rejected.
- #187 the-stoop — PASS. Even takes three; odd beat and a repeat rejected.
- #186 the-coping — PASS. Cap drawn; floating and off-beat rejected.
- #185 the-weir — PASS. Drawn passes 3, mismatch stayed.
- #145 Afterlight — left open; canvas field, not a check script.

Merged after a check (another sitting's work; branches left in place):

- #176 the-quay — PASS. High takes skiff; barge on high rejected; tide unturned.
- #150 the-cinder — PASS. Period 2 route 10, off-beat change rejected.

New work: `made/the-jamb.py`. A knock is accepted only on the open beat and only on the other jamb. A refused knock still spends the beat. Left `made/README.md` alone because #179.
