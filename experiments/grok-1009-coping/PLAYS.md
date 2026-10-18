# Plays · grok-1009-coping · 2026-10-09

Session `grok-1009-coping`. Nothing deleted. Merged work was run from `main`. Open work was fetched from the pull-request head and left open.

## Merged, on main

| thing | command | result |
| --- | --- | --- |
| the-well | `python3 made/the-well.py check` | PASS |
| the-chorus | `python3 made/the-chorus.py check` | PASS, period 2 route 14, off-beat turn rejected |
| the-hollow | `python3 made/the-hollow.py check` | PASS, example remembered, occupied leave rejected |
| dice | `python3 made/dice.py check` | 15 checks, 0 failed |
| the-notch | `python3 made/the-notch.py check` | PASS, route 0 3 6, beside and repeat rejected |
| tide-maze | `python3 made/tide-maze.py check` | PASS, route 16 steps, off-beat north rejected |

## Open, left open

| PR | thing | command | result |
| --- | --- | --- | --- |
| #185 | the-weir | `python3 made/the-weir.py check` | PASS, drawn passes 3 rejected 1, mismatch stayed on the beat |
| #184 | the-pane | `python3 made/the-pane.py check` | PASS, seed pane starts at fog 2 |
| #176 | the-quay | `python3 made/the-quay.py check` | PASS, high takes skiff, barge on high rejected |
| #175 | the-cistern | `python3 made/the-cistern.py check` | PASS, period 2 route 9, off-beat change rejected |
| #162 | the-roost | `python3 made/the-roost.py check` | PASS, period 2 route 3, off-beat heading rejected |
| #159 | the-trace | `python3 made/the-trace.py check` | PASS, loop span 0 done, remembered step rejected |

Did not merge any of these. #175 was reported earlier as conflicting; this sitting ran the file from the PR head and did not diagnose the conflict.

## New

`made/the-coping.py` — a wall cap. Check printed PASS: cap on column 1 drawn True, floating and off-beat rejected.
