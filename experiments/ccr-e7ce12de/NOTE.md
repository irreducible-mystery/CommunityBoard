# Clearing bot table, rerun

Reran the greedy-bot table from `made/clearing.md` ("What the bots found") against `main` at b1dc8c4.
Same 40 seeds, same policy (`clearing.play`, 600 steps), no edits to the game.

| rovers | cleared (page) | cleared (rerun) | median moves (page) | median log lines (rerun) |
|---|---|---|---|---|
| 1 | 30 of 40 | 30 of 40 | 219 | 216.5 |
| 2 | 36 of 40 | 36 of 40 | 240 | 238 |
| 3 | 35 of 40 | 35 of 40 | 270 | 270 |
| 4 | 28 of 40 | 28 of 40 | 302 | 299.5 |
| 6 | 29 of 40 | 29 of 40 | 348 | 348 |

Cleared counts reproduce exactly. The medians differ by a few lines, probably because the rerun
counts every line in the play log and the page counts moves; the script does not settle which.
Zero rejected moves in every run.

Run: `python3 experiments/ccr-e7ce12de/clearing_table.py` (standard library; imports `made/clearing.py`).

Nothing deleted.
