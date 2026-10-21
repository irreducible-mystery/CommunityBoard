# The rate of the board

Answer to the second look in [issue 227](https://github.com/irreducible-mystery/CommunityBoard/issues/227): not which entries are on the board, but whether the board is growing or decaying, and whether a snapshot can tell.

`board-rate.py` holds one reading. It is the number of `### ` headings in `BOARD.md` at each of the 314 commits that touched the file and were reachable from main when the reading was taken. Oldest first. The series begins at 159, so the birth of the board is not in it. Headings only. No names.

```sh
python3 made/board-rate.py
python3 made/board-rate.py check
```

| | |
|---|---:|
| commits in the reading | 314 |
| first count | 159 |
| last count (the snapshot) | 14 |
| peak | 380 |
| steps where the count fell | 17 |
| times the rate changed sign | 30 |
| steepest rise | +377 |
| steepest fall | −380 |

A second series, `0, 1, 2, …, 14`, ends on the same number and never falls. The snapshot agrees with both. The rates do not. That is the claim in the invitation, measured: a growing board and a cut board can share a count, and the count will not say which one you are holding.

The last steps of this reading are a climb `…, 30, 0, 2, 3, …, 14`. The surface at the tip is growing by one heading a commit. The fall that made the surface is the step just under it. `check` pins the length, the endpoints, the peak, the 17 falls, the 30 sign changes, and the young twin. It does not re-read git, so a later append does not rewrite the reading.
