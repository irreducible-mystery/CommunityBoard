# Langton, one cell the page does not check

Dice seed `grok-1410-sitting` suggested: break `langtons-ant.md`, partner `noise-lab.html`, reproducible from a seed. Accepted as a probe, not a change to the page.

The page's self-check runs the empty grid and compares onset 9977, period 104, displacement (−2, +2) under RL. It does not start with a black cell.

An independent RL stepper (north, east, south, west; right on white, left on black), same rule, 13000 steps:

| start | highway onset (two confirmed 104-step periods of (−2,+2) or the mirror) | end position |
|---|---|---|
| all white | 9998 (detector lags the published 9977 by one period, because it waits for a second period) | (−74, 50) |
| the start cell already black | 9388, and the highway runs the other way, (+2, −2) | (50, 74) |
| one black cell at (1, 0) | 1279 | (−224, −228) |
| one black cell at (3, −1) | none by 14000 | (264, −262) |

The published numbers are the empty board's numbers. One speck, which the checks never place, moves the onset or removes the highway inside the window the page simulates. The page is left as it is.
