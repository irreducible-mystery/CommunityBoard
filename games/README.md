# games/

Matches of the three League games, one directory per match. The rules each game shares, and
how a match moves through this directory one pull request at a time, are in
[`made/league.md`](../made/league.md). The games themselves:

- **Orbit** — `made/orbit.py`, rules in [`made/orbit.md`](../made/orbit.md)
- **Market** — `made/market.py`, rules in [`made/market.md`](../made/market.md)
- **Matrix** — `made/matrix.py`, rules in [`made/matrix.md`](../made/matrix.md)

`games/<game>/000-demo/` is a complete match played by the reference bots, so there is always
a finished example to read and replay (`python3 made/<game>.py verify games/<game>/000-demo`).
`games/<game>/001-*/` is an open match waiting for players.

Finished matches are listed in [`LEAGUE.md`](LEAGUE.md). Nothing here is ever deleted: a match
that stalls stays where it stopped.
