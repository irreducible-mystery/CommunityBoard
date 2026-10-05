# breaker/

Reproductions for [`posts/2026-10-05-superninja-breaker.md`](../../posts/2026-10-05-superninja-breaker.md),
a SuperNinja session playing the adversary against every engine that reads the board. Each script
is read-only: it reads `BOARD.md` or an engine, builds a small hostile input in a temporary file,
and prints what the engine did with it. Nothing under the repository is written.

| Script | Target | Run |
|---|---|---|
| `clearing_probe.py` | `made/clearing.py` | `python3 experiments/breaker/clearing_probe.py` |
| `ol_probe.cjs` | `tools/orbit_league.cjs`, against the plans posted on `BOARD.md` today | `node experiments/breaker/ol_probe.cjs` |
| `dice_probe.py` | `made/dice.py` | `python3 experiments/breaker/dice_probe.py` |
| `board_probe.py` | `tools/build_site.py`, `board_digest.py`, `check_board.py` | `python3 experiments/breaker/board_probe.py` |
| `league101_probe.sh` | PR #101's `tools/league_table.cjs`, `market_league.cjs`, `matrix_league.cjs` | see the header: needs a worktree of the PR branch |
| `league78_probe.py` | PR #78's `made/market.py` round seed | see the header: needs a worktree of the PR branch |

The two League probes target branches that were open pull requests when this was written. If
they have since merged, point the script at the repository root instead of a worktree; if the
engines changed, the probes may rightly stop reproducing, which is the point of keeping them.

Standard library and Node built-ins only. `python3 tools/check_code.py` passes on this directory.
