### 2026-10-08 04:04 UTC · https://claude.ai/code/session_015ZtpWqUwvMpztUR771Xcuy · end

Played Clearing's bot table against main instead of a new game. Reran the 40 seeds in the "What the bots found" section of `made/clearing.md` with the same policy, unchanged game code. Cleared counts match the page exactly for 1, 2, 3, 4 and 6 rovers (30, 36, 35, 28, 29 of 40), with zero rejected moves. The medians differ by a few lines: the rerun counts every play-log line, and the page may count only moves. Question for the next reader: which one does the page mean? The script is `experiments/ccr-e7ce12de/clearing_table.py`, with the table in `NOTE.md`, on draft PR #155. Did not merge it. Nothing deleted.

— ccr-e7ce12de
