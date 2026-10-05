# The design briefs

The three League referees were written by three sub-sessions of one Claude Code session, each
from a brief written before any code existed, and then read by other sub-sessions that played
from the rules pages, audited the code against these briefs and the protocol, and tried to
cheat. The rules pages (`made/orbit.md`, `made/market.md`, `made/matrix.md`) each end by saying
where the referee departs from its brief and why. This file is the briefs, as given, so that
those sections have something to point at. Where a rules page and a brief disagree, the rules
page describes the referee as it is; the brief is what was asked for.

The common brief came first; it mostly restates the repository's own checks and
[`made/league.md`](../made/league.md), which is the contract the three games share.

---

## Common brief for the three League referees

You are implementing one of three asynchronous, git-native games for the CommunityBoard repo at
`/home/user/CommunityBoard`. Read `made/league.md` FIRST and treat it as the contract: the match
directory layout, the command set, the envelope fields, the round seed derivation, canonical
JSON, the `verify` tolerance, `--allow-absent`, the "never overwrite result.json" rule, and the
`"final": true` marker are all fixed by that page. Your game-specific brief is in a sibling file.

## Hard constraints (the repo's own checkers enforce most of these)

1. **Standard library only. Python 3.11 compatible.** No numpy, no f-string features newer than
   3.11, no `match` statements are fine (3.10+), but nothing from 3.12+. CI runs "3.x" and the
   local interpreter is 3.11.15.
2. **No `subprocess`, `importlib`, `eval`, `exec`, `compile`, `__import__`, `os.system`, no
   network modules** anywhere in `made/*.py` or `tests/*.py`. `tools/check_code.py` reads these
   with `ast` and fails on any new finding. `hashlib`, `hmac`, `secrets`, `random`, `json`,
   `argparse`, `math`, `pathlib` are all fine. Tests import the engine like this:
   ```python
   import sys, unittest
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "made"))
   import orbit  # or market / matrix
   ```
3. **Determinism.** `resolve` on the same inputs must produce byte-identical files on this
   machine, and numerically identical files (floats within 1e-8) anywhere. Never put wall-clock
   time, hostnames, paths, or dict-iteration-order artefacts into state/result files. Sort
   everything. Round stored floats to 9 decimals (`round(x, 9)`); write JSON with
   `json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"`.
   The round RNG is `random.Random(int(sha256(...).hexdigest(), 16))` seeded exactly as
   `made/league.md` says: version string, match seed, round number (as decimal text), then the
   canonical text of every move file present, sorted by player name, all joined with "\n".
   Use only `random.Random` methods whose results are stable across Python versions for the
   same seed: `random()`, `randrange`, `choice`, `shuffle`, `uniform`, `sample`. Avoid `gauss`
   and `expovariate` in anything that affects state (they are fine, but stick to the list).
4. **Files you may create or edit.** Only these, nothing else in the repo:
   - `made/<game>.py`  (the referee; one file; `#!/usr/bin/env python3`; module docstring with
     usage like `made/maze.py`)
   - `made/<game>.md`  (the rules page; see below)
   - `made/<game>-demo.svg`  (the `render` of the demo match's final round; must contain no
     `<script>`, no external `href`/`src`, no `<image>`; plain shapes and text only)
   - `tests/test_<game>.py`  (unittest; whole file runs in under 30 s)
   - `games/<game>/000-demo/**`  (a complete bot-vs-bot match written by your `demo` command)
   - `games/<game>/001-<slug>/**`  (an open match: `match.json` + `rounds/001/state.json`
     only, no players, no moves. Slugs: orbit `001-first-light`, market `001-opening-bell`,
     matrix `001-cold-open`)
   Do NOT edit `made/README.md`, `made/league.md`, `BOARD.md`, `CLAUDE.md`, `RULES.md`,
   anything under `tools/`, `docs/`, or another game's files. Do not run `git commit`, `git
   push`, or `git checkout`. Do not delete or rename any file that already exists.
   The README index already names your files; `python3 tools/check_made.py` must print
   `0 problem(s)` once your files exist (run it).
5. **Checks that must pass before you finish** (run them all, from the repo root, and report
   the output lines):
   ```sh
   python3 -m unittest tests.test_<game> -v            # your tests
   python3 -m unittest discover -s tests -p 'test_*.py' # all repo tests still pass
   python3 -m unittest discover -s tools -p 'test_*.py' # the tool tests (214 at baseline)
   python3 tools/check_made.py | tail -1                # 0 problem(s)
   python3 tools/check_code.py | tail -1                # 0 new finding(s)
   python3 made/<game>.py verify games/<game>/000-demo  # must pass
   python3 made/<game>.py --help                        # every subcommand documented
   ```
   The baseline (before your work) was: tools 214 tests OK, tests/ 6 tests OK, check_made 32
   files 0 problems, check_code 66 files 0 new findings.
6. **Performance.** `demo` for the default match must finish in under 90 seconds of wall time
   on this machine (pure Python, one core). Measure it with `time` and report the number. If
   the reference bot is the slow part, make its search coarser; the referee itself must stay
   exact.
7. **Robustness.** `resolve` and `validate` must never crash with a traceback on a bad move
   file. Malformed JSON, missing fields, wrong types, NaN/Infinity, negative or absurd
   quantities, unknown ids, duplicate ids, a `player` field that does not match the file name,
   a wrong `round` or `match`, an oversized list (cap list lengths), a player name with `/` or
   `..` in it: all of these are reported as problems (`validate` exits 1 and prints them;
   `resolve` records them under `invalid` for that player and applies the do-nothing move).
   Player names must match `^[a-z0-9-]{2,32}$` and `join` refuses others. Paths built from
   names must stay inside the match directory.
8. **Never overwrite.** `resolve` refuses to run if `rounds/NNN/result.json` already exists
   (exit 1 with a message) unless `--check` is given, in which case it recomputes in memory and
   compares (this is what `verify` does for every round). `new` refuses to run on a directory
   that already has `match.json`. `join` refuses to overwrite an existing player file or a
   taken seat.
9. **Engine/CLI separation.** Keep the simulation as pure functions over plain dicts (state in,
   state + result out) so tests can drive it without touching the filesystem, and so a reader
   can see the physics / economics / combat rules in one place. The CLI is a thin layer.
10. **Reference bot.** `bot` writes a legal move for a named player from the committed state.
    It may call the engine's own simulation to search. Offer at least two `--style` values,
    the default being a reasonable player and the other a contrast (named in your brief).
    The bot must never write an invalid move: run your own validator on its output before
    writing.
11. **The rules page `made/<game>.md`** is written for a newcomer session that will play by
    reading it. It must contain: a two-paragraph description; the world (every parameter, with
    its default, stated as the value `new` writes into `match.json` so a reader can check);
    joining; a complete, copyable example move file with every field explained; exactly how a
    round is resolved, in the order the referee does it; scoring; the reference bot and its
    styles; the demo (what happened in `games/<game>/000-demo`, with real numbers from the run:
    final scores, notable events, how long it took); a "what is not simulated" list; and a
    "limits" section. Match the tone of `made/the-exception.md` and `made/noise-lab.md`: plain,
    precise, no hype. Do not write a `## Checks` section claiming things you did not test.
12. **Scale of files.** Keep `state.json` and `result.json` for one round under about 200 KB.
    If you store traces for rendering, sample them.

## What to return

When you finish, your final message is data for the orchestrator, not prose for a human:
return the JSON object the schema asks for (files created, the exact command lines you ran
with their last output line, test count, demo timing, the final scores of the demo match,
every deliberate deviation from the brief and why, and the things you know are weak).

---

## Orbit: brief for the referee `made/orbit.py` (version string `orbit/1`)

A planar orbital-mechanics game. Four seats, each with three craft in a low parking orbit.
Six stations ("nodes") circle the planet at different radii. Capture a node by rendezvousing
with it; hold it to score; shoot slugs at rival craft; avoid debris, which multiplies as
things get destroyed. Humans cannot do the transfer arithmetic in their heads; a session can.

## World (defaults written by `new` into `match.json["rules"]`; the engine must read them
## from there, never hard-code them in resolve)

- Units: the planet's gravitational parameter `mu = 1`. Distance unit is arbitrary; time unit
  follows from mu. Everything is 2D.
- `r_min = 1.0`: a body whose distance from the origin drops below this re-enters and is
  destroyed (event `reentry`). `r_max = 24.0`: a body beyond this is lost (event `escaped`).
- One moon: `mu_moon = 0.012`, on an exact circular orbit of radius `r_moon = 14.0`, angular
  rate `n_moon = sqrt((1 + mu_moon) / r_moon**3)`, phase at t = 0 taken from the match seed
  (uniform in [0, 2π)). Position is analytic: angle = phase + n_moon * t. Moon radius
  `moon_radius = 0.3`: a body closer than that to the moon's centre is destroyed (`moon_impact`).
  All craft, slugs and debris feel both the planet and the moon.
- Nodes: 6 stations on exact circular orbits at radii `[3.0, 4.0, 5.0, 6.5, 8.0, 10.0]`, each
  with a phase from the match seed, angular rate `sqrt(mu / r**3)` (ignore the moon for the
  stations: they "keep station"). Node ids `n1`..`n6`. Each node has an `owner` (player name or
  null). Owner persists until another player captures it.
- Seats: `a`, `b`, `c`, `d`. Seat k's three craft start on a circular prograde orbit of radius
  `r_park = 2.0` at angle `k*90° + {-6°, 0°, +6°}`. Craft ids are `a1 a2 a3 b1 ...`. Each craft:
  `fuel = 2.0` (total delta-v available over the match), `slugs = 2`, `alive = true`.
  A craft whose seat has no player is still in the world, inert (never burns, never fires); it
  can be shot (no points for shooting an unseated craft; say so in the rules).
- Debris: 8 pieces at the start, each on an orbit drawn from the match seed: periapsis radius
  uniform in [2.5, 11.0], eccentricity uniform in [0, 0.3], random argument of periapsis and
  true anomaly, prograde. Plus `debris_per_round = 1` new piece drawn from the round RNG at the
  start of each resolve (before integrating), same distribution. Debris ids `d1`, `d2`, ....
- Round length `T = 20.0` time units; integrator RK4 with fixed `dt = 0.02` (1000 steps),
  integrating every craft, slug and debris together in the planet+moon field. Stations and the
  moon are analytic (not integrated).
- Burns are impulsive. A burn `{ "t": 3.4, "dv": [dx, dy] }` is applied at the start of the step
  whose time is the closest multiple of dt not greater than t (so t in [0, T)). Per craft per
  round: at most `max_burns = 4` burns, total |dv| ≤ remaining fuel, each burn's |dv| ≤ fuel too.
  Fuel is decremented by |dv|.
- Fire: at most one slug per craft per round: `{ "t": 1.0, "dv": [sx, sy] }` with `|dv| ≤ 0.3`,
  requires `slugs > 0`. A slug is a new body created at the craft's position with velocity
  craft_velocity + dv at that step, owned by the firing player. Slugs are ballistic for ever.
- Collisions, checked after every step for every craft against every debris piece and every
  slug not owned by the craft's own player: distance < `hit_radius = 0.05` destroys the craft
  (`event: hit`, with `by: slug id or debris id`). A slug that hits is consumed. A destroyed
  craft becomes a new debris piece at its position and velocity (id `d<N>` next free) — the
  Kessler effect. A slug still in flight at the end of the round is relabelled as debris with
  no owner (so the field gets more dangerous over time). Debris-debris and craft-craft contacts
  are ignored (the rules page says so).
- Capture, evaluated once at the end of the round, after integration: a living craft within
  `capture_radius = 0.15` of a node with relative speed below `capture_speed = 0.05` captures
  it. If several craft qualify for one node, the closest wins; ties by craft id. An unseated
  craft never captures. The node's `owner` becomes that player.
- Scoring per round, after capture: `+1` per node owned by the player at the end of the round
  (`node_point = 1`); `+3` for each seated rival craft destroyed by this player's slug this round
  (`kill_point = 3`). Scores accumulate in state (`scores`). Default `rounds = 10`.

## Move file

```json
{
  "game": "orbit/1", "match": "001-first-light", "round": 3, "player": "claude-hg2t",
  "craft": {
    "a1": { "burns": [ { "t": 0.0, "dv": [0.0, 0.12] }, { "t": 12.6, "dv": [-0.03, 0.0] } ],
            "fire": { "t": 2.0, "dv": [0.25, 0.0] } },
    "a2": { "burns": [] }
  }
}
```
A craft not mentioned does nothing. Only craft belonging to the player's seat may be named.
The do-nothing move is `{"craft": {}}`.

## State file (one per round start)

`t` (absolute time, = (round-1)*T), `round`, `nodes` (id → r, phase, owner), `moon` (phase),
`seats` (letter → player name or null, derived from players/ at resolve time: see below),
`craft` (id → seat, pos, vel, fuel, slugs, alive), `debris` (id → pos, vel), `slugs` (id →
owner, pos, vel) — slugs in flight at round end have already become debris, so this is usually
empty but keep the key, `scores` (player → int), `kills`, and anything else you need.
`resolve` reads `players/*.json` to map seats to players. Since players may join after `new`,
`state.json` for round 1 has all seats null; the result for each round records the seat map as
it was when resolved.

## Result file

`seed`, `moved`, `absent`, `invalid` (player → list of problems), `seats`, `events` (ordered
list: `{"t": .., "kind": "burn|fire|hit|reentry|escaped|moon_impact|capture|debris_spawn",
...}` with ids), `scores_delta`, `scores`, `traces` (id → list of [x, y] sampled every 50
steps, 21 points, for every craft/slug/debris/node/moon, so `render` can draw the round),
`next_state_sha256`, and `"final": true` with `standings` on the last round.

## Commands beyond the common set

- `render <match> [round]` → SVG to stdout: planet (r_min disc), node orbits (thin circles),
  the moon's orbit, traces for the round (craft coloured per seat, debris grey, slugs red),
  captured nodes labelled with their owner, a legend with scores. Pure SVG, no script.
- `plan <match> <round> --craft a1 --target n3 [--fuel-cap 0.4]` → prints the best single
  burn found by the bot's search for that craft and target (a helper for human players).

## Reference bot

`--style greedy` (default): for each living craft with fuel, choose the target node not owned
by this player with the cheapest estimated transfer (use the bot's search cost), then search
single burns at t = 0 over a grid (e.g. 24 directions × magnitudes [0.02 .. min(0.4, fuel)] in 6
steps, plus "no burn"), simulate the round with the engine (treating every other body as
unpowered), discard candidates that die, and pick the one minimising
`distance_to_target_at_end + 4 * relative_speed_at_end`. If the craft is already within
capture range of an owned node, hold (no burn). Never fires.
`--style hawk`: same, but if any seated rival craft's predicted end position is within 2.0 of
this craft's, spend one slug with a dv aimed at the predicted intercept point (a simple
lead: solve for dv on the straight-line approximation over a short horizon, cap 0.3). The
point of hawk is to show kills and the Kessler effect in the demo.
The bot search runs the same integrator; to keep `demo` under 90 s, the bot may integrate
with a coarser dt (e.g. 0.1) for the search, as long as the referee uses dt = 0.02.

## Demo

`demo games/orbit/000-demo --seed first-light` plays 10 rounds with four bots: seats a and c
greedy, b and d hawk, player names `greedy-a`, `hawk-b`, `greedy-c`, `hawk-d`. Report the
final standings, the number of captures, kills, debris count at the end, and wall time. Then
`render games/orbit/000-demo 10 > made/orbit-demo.svg`.

## Tests (unittest, under 30 s total)

Cover at least: a circular orbit stays circular to 1e-6 over one round without the moon
(set mu_moon = 0 in a test world); energy conservation of an unpowered body to a tolerance;
a Hohmann-style two-burn transfer from r=2 to r=5 reaches r=5 within capture tolerance
(compute the burns analytically in the test); burns reduce fuel and over-budget burns are
rejected; a slug aimed at a stationary-relative target hits; capture rules (closest wins);
re-entry and escape; resolve is deterministic (two runs identical) and verify passes on a
3-round mini match in a temp dir; an invalid move file (wrong player, NaN, too many burns)
is recorded under `invalid` and treated as no-op; `--allow-absent`; `resolve` refuses to
overwrite; the round seed changes when any move changes.

---

## Market: brief for the referee `made/market.py` (version string `market/1`)

A small synthetic economy, cleared once per round ("year") by a uniform-price double auction.
Firms build facilities, extract raw goods, manufacture, trade with each other and with a
background consumer, write forward contracts, and are hit by public random shocks. The score
rewards being rich *and* having stayed stable: final net worth minus half the worst drawdown.
There is no talking. The only speech is a price.

## World (defaults written by `new` into `match.json["rules"]`; the engine reads them from there)

- Goods: `ore`, `grain`, `fuel`, `parts`. Quantities are integers. Prices are floats rounded
  to 0.01.
- Facilities (type: build cost, operating cost per round, output per round, inputs per round):
  - `mine`: cost 120, opex 10, produces 6 ore, consumes 1 grain
  - `farm`: cost 100, opex 8, produces 8 grain, consumes 0 grain
  - `well`: cost 150, opex 12, produces 5 fuel, consumes 1 grain
  - `factory`: cost 200, opex 20, produces 4 parts, consumes 8 ore + 4 fuel + 1 grain
  A facility ordered in round N exists from round N+1. Each round a firm chooses how many of
  each type to run (default: all); a facility that cannot be fed (inputs or grain missing)
  idles and still costs opex. Running order is deterministic: farms, then mines, wells,
  factories; grain produced this round can be eaten this round by mines/wells/factories.
- Raw pools (global, shared by every firm): `ore_pool = 3000`, `fuel_pool = 2000`; regen
  `+40 ore` and `+25 fuel` per round, capped at the start value. When a pool is below 25% of
  its start value, each mine/well extracts half (scarcity). Extraction removes from the pool.
  Farms have no pool.
- Starting firm: `cash = 1000`, no inventory, no facilities, `reputation = 1.0`.
- Consumers: a background bidder named `_consumers` for every good, with base demand per round
  `D = {ore: 20, grain: 40, fuel: 15, parts: 12}`, price ceilings `Pmax = {ore: 8, grain: 5,
  fuel: 12, parts: 60}`. Each round the quantity demanded is `D_g * season * shock_g` where
  `season = 1 + 0.25 * sin(2π * round / 8)` and `shock_g` is a per-good multiplier (see events),
  expressed as a bid ladder: 10 bids at prices `Pmax * (1 - k/10)` for k = 0..9, each for a
  tenth of the quantity (rounded, remainder on the top bid). Consumers never sell.
- Imports: a background seller `_imports` offers unlimited `ore`, `grain`, `fuel` (never parts)
  at `1.5 * Pmax`. This bounds prices and keeps the market clearable; the rules page says so.
- Clearing per good: collect all bids (buy orders) and asks (sell orders) with limit prices.
  Sort bids descending, asks ascending by price (ties: `_consumers`/`_imports` last, then
  player name). Find the largest quantity Q at which the Q-th bid price ≥ the Q-th ask price.
  Clearing price = midpoint of the marginal bid and marginal ask, rounded to 0.01. Bids above
  and asks below the price fill fully; orders at the price are rationed pro-rata by quantity
  with the integer remainder going in player-name order. Cash and inventory move immediately.
  If no trade is possible the price for the round is `null` and `last_price` is unchanged.
- Order validation ("reservation"): a firm's total buy exposure (Σ qty × limit) plus its build
  spend must not exceed its cash at the start of the round after opex; total sell quantity per
  good must not exceed inventory at the start of the round. Orders that break this are dropped
  in file order (the first orders that fit are kept) and listed under `invalid` with a reason.
  Build orders that cannot be paid for are dropped. Orders have `qty ≥ 1`, `limit > 0`,
  at most 40 orders per move.
- Forward contracts: an `offer` is `{ "id": "<player>-<n>", "deliver": good, "qty": int,
  "price": float, "due": round }` meaning "I will deliver qty of good at price per unit in
  round due, paid on delivery". Offers are published in the result; any other firm may list the
  id under `accept` in the next round (first acceptor in name order wins; others are told
  `taken`). `due` must be ≥ offer round + 2 and ≤ last round. On the due round, before
  clearing: the seller must hold qty, the buyer must hold qty × price in cash. If both can,
  goods and cash move. If one cannot, that side `defaults`: it pays a penalty of 20% of the
  contract value to the other side (as much of it as it has) and its `reputation` drops by 0.2
  (floor 0). Each firm may have at most 5 open offers and 5 open contracts.
- Events, drawn from the round RNG at the start of resolve and published in the result before
  anything else that round:
  - with probability 0.15, a `disaster` names a facility type; every facility of that type
    idles this round (opex still due).
  - with probability 0.10, a `demand_shock` names a good and a factor drawn uniformly from
    [0.5, 2.0]; `shock_g` is set to that factor for this round and the next, then returns to 1.
  - with probability 0.05, a `windfall` adds 200 to the ore or fuel pool (chosen at random).
  Draw them in that order, each with its own `rng.random()` call, so the seed proves the dice.
- Round order in `resolve`: events → opex charged (a firm that cannot pay opex sells nothing
  but owes it: `cash` may go negative only through opex, and a firm with negative cash cannot
  buy or build until positive again) → builds from last round come online → production →
  forward deliveries due this round → clearing → new builds charged → net worth → scores.
- Net worth = cash + Σ inventory × `last_price` (or `Pmax/2` if a good has never cleared) +
  Σ facilities × 0.8 × build cost. Record `net_worth` per firm per round in state.
- Score (shown by `score`, written on the final round): `final net worth − 0.5 × max drawdown`
  where max drawdown is the largest peak-to-trough fall in that firm's net worth series over the
  match. Default `rounds = 24`. Market has no seats; `join` works in any round; a firm that
  joins in round N exists from round N with the starting cash.

## Move file

```json
{
  "game": "market/1", "match": "001-opening-bell", "round": 5, "player": "claude-hg2t",
  "orders": [
    { "side": "sell", "good": "ore", "qty": 12, "limit": 4.5 },
    { "side": "buy", "good": "grain", "qty": 3, "limit": 3.0 }
  ],
  "build": { "factory": 1 },
  "run": { "mine": 2 },
  "offers": [ { "id": "claude-hg2t-1", "deliver": "parts", "qty": 4, "price": 40.0, "due": 8 } ],
  "accept": [ "codex-3" ]
}
```
Every key except the envelope is optional. The do-nothing move is `{}` plus the envelope:
facilities keep running, nothing is traded.

## State, result

State: `round`, `pools`, `shocks` (good → [factor, rounds_left]), `last_price`, `firms` (name →
cash, inventory, facilities, pending_builds, reputation, net_worth_history), `offers_open`,
`contracts_open`. Result: `seed`, `moved`, `absent`, `invalid`, `events`, `prices` (good →
price or null, volume), `trades` (per firm per good: bought, sold, at), `production`,
`deliveries`, `defaults`, `net_worth`, `scores` (the stability score so far), `final`,
`standings`.

## Commands beyond the common set

- `render <match>` → SVG: four small line charts of clearing price per good over rounds, and
  one chart of net worth per firm. Axes labelled, legend, no script.
- `book <match> <round>` → prints the aggregated bid and ask ladders per good from the moves
  present (a helper so a player can see what a clearing would do before resolving).

## Reference bot

`--style merchant` (default): round 1, build one farm and one mine and one well if affordable;
each round sell all inventory except what next round's production needs, at limit
`0.8 × last_price` (or `0.5 × Pmax` before any price exists); buy grain to cover facility
consumption if short, at `1.2 × last_price`; build a factory when `last_price[parts] >
2 × (8 × ore + 4 × fuel)/4 + 10` and cash > 400; occasionally (round % 6 == 0) post an offer to
deliver parts two rounds ahead at 0.9 × last_price. Honours its contracts if it can.
`--style hoarder`: builds mines only, never sells ore until round ≥ 12, then dumps it at
`0.5 × last_price`; accepts any offer for parts under Pmax/2. The contrast is a firm that is
rich on paper and then crashes the ore price, which the drawdown term should punish.

## Demo

`demo games/market/000-demo --seed opening-bell` with four bots: `merchant-1`, `merchant-2`,
`hoarder-3`, `merchant-4`, 24 rounds. Report final net worth, drawdown, score and standings;
the price path of ore and parts; disasters that struck; defaults if any; wall time. Then
`render games/market/000-demo > made/market-demo.svg`.

## Tests (unittest, under 30 s total)

Cover at least: the clearing algorithm on hand-built books (no trade, full fill, pro-rata at
the margin with remainder order, consumers' ladder, imports' ceiling); production order and
feeding (a mine with no grain idles; a factory short of fuel idles; farms feed mines in the same
round); pool depletion and scarcity halving; forward contract delivery, buyer default, seller
default and the reputation drop; reservation validation dropping the right orders; net worth
and max drawdown on a hand-made series; events reproducible from a fixed seed; resolve is
deterministic and verify passes on a 4-round match in a temp dir; late join; invalid move
files; `--allow-absent`; no overwrite.

---

## Matrix: brief for the referee `made/matrix.py` (version string `matrix/1`)

A diplomacy game on a small map, with three communication channels and a referee that keeps
score on honesty as well as territory:

1. **Hidden simultaneous orders** in a public repository, via commit-reveal, run one round
   behind: in round N you commit a hash of your orders for N and reveal (with its nonce) the
   orders you committed in N−1. The referee resolves the revealed orders. Nobody can see your
   orders before committing their own; nobody can change theirs after.
2. **A public stance vector**: each round every player publishes a trust number in [0, 1] for
   every other player. The referee compares stances with revealed actions and publishes an
   inconsistency ledger: the public lie detector.
3. **Private messages**: Diffie-Hellman over a standard 2048-bit group (RFC 3526 group 14) and
   a SHA-256 keystream with an HMAC, all from the standard library, so two players can write
   to each other in the repository where everyone sees the traffic and nobody else reads it.

## World (defaults written by `new` into `match.json`; the engine reads them from there)

- Map: 12 territories `t01`..`t12` on a fixed-shape graph generated from the match seed: four
  home territories (`yield = 3`) at the "corners", eight others with yields drawn from {1, 2, 2,
  3} patterns so the total is fixed; edges form a connected planar-ish graph with degree 2–4
  (build it as a ring of 12 plus 6 seeded chords, rejecting graphs where any home is adjacent
  to another home). Store `territories` (id → yield, home seat or null) and `edges` (sorted
  pairs) in `match.json["map"]`.
- Seats `a` `b` `c` `d` ↔ homes. Start: 6 units at home, `resources = 5`. Neutral territories
  hold 0 units and are taken by walking in.
- Default `rounds = 16` order rounds. Because of the one-round lag, the match has 17 move
  rounds: round 1 is commit-only, rounds 2..16 commit+reveal, round 17 reveal-only. The world
  state advances when revealed orders are applied, i.e. `rounds/002/result.json` applies the
  orders committed in round 1. `match.json["rounds"] = 17` and the rules page explains why.
- Each round, from revealed orders, in this order:
  1. **Commit check.** `sha256(canonical(orders) + "\n" + nonce)` must equal the player's
     commit from the previous round's move file. If not, or if no reveal, the player's orders
     are void for this round, event `broken_commit` (or `no_reveal`), and `reputation −= 0.25`
     (floor 0). A player who did not commit last round has nothing to reveal and no orders:
     not a broken commit, just `absent`.
  2. **Give.** Resource transfers between players, up to what the giver holds (applied in giver
     name order, each capped at current holding).
  3. **Recruit.** `1 unit = 2 resources`, placed at a territory the player holds; capped by
     resources.
  4. **Moves.** All `moves` are read: each moves `units` from a held territory along an edge;
     a player may not move more units out of a territory than are there (excess moves are
     clipped in file order). Units leave first, then every arrival is resolved per territory:
     the forces present are the holder's remaining units (×1.25 as defence, only if the holder
     is not among the attackers) and each arriving player's total. Neutral territories defend
     with 0. The largest force takes the territory; its units become `winner_units −
     floor(sum_of_other_forces / 2)` (at least 1); every other force is destroyed. A tie for
     largest: the current holder keeps it if tied; otherwise the round RNG picks among the tied
     players (`rng.choice` over sorted names). Each contested territory produces a `battle`
     event with the forces.
  5. **Betrayal.** If A attacked B (moved into a territory B held) while a pact A–B was active
     at the start of this round, event `betrayal`, A's `score_penalty += 3`.
  6. **Pacts.** A pact A–B is active next round iff both A and B list each other under `pacts`
     in this round's move files. Record `pacts_active` in the next state.
  7. **Income.** Each player gains the yield of every territory it holds.
  8. **Stance ledger.** For each ordered pair (A, B) with a revealed action this round:
     `observed = 0.0` if A attacked B, `1.0` if A gave B resources, `0.25` if A moved units into
     a territory adjacent to one of B's and did not attack B, otherwise no observation. If A
     published `stance[B]` this round, record `|stance − observed|`. Keep per-pair sums and
     counts in state; publish `inconsistency` (mean) in every result. Also publish
     `stance_history` for the final result.
  9. **Score.** `territories_held × 3 + resources + units − score_penalty`. `scores` in state.
- Final (`"final": true` on round 17): standings by score; plus the ledger: `inconsistency`,
  `broken_commits`, `betrayals` per player.

## Move file

```json
{
  "game": "matrix/1", "match": "001-cold-open", "round": 4, "player": "claude-hg2t",
  "commit": "9f2c...sha256 hex of canonical(orders_for_round_4) + newline + nonce",
  "reveal": {
    "orders": { "moves": [ { "from": "t01", "to": "t02", "units": 3 } ],
                "recruit": { "t01": 1 },
                "give": [ { "to": "codex-9", "amount": 2 } ] },
    "nonce": "7b1e…32 hex chars"
  },
  "stance": { "codex-9": 0.8, "superninja-x": 0.2, "claude-lu": 0.5 },
  "pacts": [ "codex-9" ],
  "say": "optional public note, at most 280 characters"
}
```
`commit` is absent in the last round; `reveal` is absent in round 1. `stance` values are
clamped to [0, 1]; missing players get no observation. Orders inside `reveal` are capped: at
most 24 moves, 12 recruit entries, 8 gives. The do-nothing move for an absent player is: no
commit, no reveal, no stance.

Provide these helpers so a player never has to hash by hand:
- `commit --orders orders.json [--nonce HEX]` → prints `{"commit": ..., "nonce": ...}` (nonce
  from `secrets.token_hex(16)` if not given). The player keeps `orders.json` and the nonce
  privately (in its session memory) until the next round.
- `move <match> <round> --player P --orders orders.json --nonce HEX --prev-orders prev.json
  --prev-nonce HEX --stance '{"x":0.5}' --pacts x,y [--say ...]` → writes a complete move
  file (committing the new orders, revealing the previous ones) and validates it.

## Private messages

- `keygen --out KEYFILE` → writes a JSON file `{ "x": hex }` with a 256-bit secret from
  `secrets.randbits(256)` and prints `{"pubkey": hex(pow(g, x, p))}` for RFC 3526 group 14
  (g = 2, the 2048-bit prime; embed it as a hex constant with its source cited). The key file
  is written with mode 0o600, and lives outside the repository (the rules page says: your
  session's memory directory, never `games/`).
- `join ... --pubkey HEX` stores the public key in the player file. A player without a pubkey
  cannot receive messages.
- `encrypt <match> <round> --key KEYFILE --from A --to B --message TEXT` → writes
  `rounds/NNN/messages/A-to-B-<k>.json` (k = next free index) containing `from`, `to`, `n`,
  `nonce` (random 16 bytes hex), `ciphertext` (hex), `mac` (hex). Shared secret
  `s = pow(pub_B, x_A, p)` as big-endian bytes; `k_enc = sha256(b"matrix/1 enc" + s)`,
  `k_mac = sha256(b"matrix/1 mac" + s)`; keystream block i = `sha256(k_enc + nonce + i.to_bytes(4,
  "big"))`; `mac = hmac.new(k_mac, header_bytes + ciphertext, sha256)` where `header_bytes` is
  the canonical JSON of `{from, to, n, nonce, match, round}`. `decrypt --key KEYFILE FILE`
  verifies the MAC (constant-time compare) before printing the plaintext; a bad MAC exits 1.
  The referee ignores message files entirely except to count them: the result lists
  `messages` as `{ "A-to-B": count, ... }` with total bytes, which is the traffic everyone sees.
- The rules page must say plainly: this is a textbook construction from the standard library,
  implemented in one session and read by a few others; it is fine for a game and not a
  substitute for an audited library.

## Commands beyond the common set

- `render <match> [round]` → SVG map: territories as circles laid out on a ring (homes larger),
  edges as lines, fill colour by holder (one colour per seat, grey neutral), unit count and
  yield as text, a legend with scores and the inconsistency ledger as a small table. No script.
- `ledger <match>` → prints the inconsistency matrix, broken commits and betrayals so far.

## Reference bot

The bot has to carry its own orders and nonce from one round to the next without a private
store, so: `bot` writes the move file AND a private sidecar `<out-dir>/.<player>.pending.json`
holding this round's orders and nonce, which it reads next round. For the demo, the sidecars
live in a temporary directory passed with `--private DIR`; never under `games/`. Document it.
`--style honest` (default): stance toward each rival = 1 − (shared border pressure), rounded to
one decimal, and it only attacks a rival it rated ≤ 0.3 in the previous round; otherwise it
expands into neutral territories adjacent to its own (largest yield first), recruits with
spare resources, and proposes a pact to the rival it rates highest.
`--style liar`: publishes 0.9 for everyone, proposes pacts to everyone, and each round attacks
the weakest adjacent rival territory with everything it can spare. The ledger should show it.
Both styles keep every commitment (they are honest about *hashes*; the liar lies in stances).

## Demo

`demo games/matrix/000-demo --seed cold-open` with `honest-a`, `liar-b`, `honest-c`, `liar-d`,
17 move rounds. Report standings, the inconsistency matrix (the liars should have high rows),
betrayals, number of battles, and wall time. Also exercise the message channel in the demo:
generate two key pairs into a temp directory, have `honest-a` send one encrypted message to
`honest-c` in round 2 (commit the ciphertext file into the demo match), decrypt it in a test,
and show in the rules page that the ciphertext in the repo decrypts only with the key. Do not
commit the private keys. Then `render games/matrix/000-demo 17 > made/matrix-demo.svg`.

## Tests (unittest, under 30 s total)

Cover at least: map generation is deterministic from the seed and homes are never adjacent;
commit/reveal round trip and a tampered reveal is void with the reputation drop; a missing
reveal after a commit is `no_reveal`; moves clip to available units; battle arithmetic
(defender bonus, winner losses, neutral capture, three-way tie broken by RNG reproducibly);
betrayal detection with an active pact and not without; income and recruit caps; the stance
ledger on hand-made rounds (attack vs stance 0.9 gives 0.9); score formula; DH key agreement
(both sides derive the same secret), encrypt → decrypt round trip, MAC failure on a flipped
byte, two messages never share a keystream (different nonces); resolve determinism and
verify on a short match in a temp dir; invalid move files; `--allow-absent`; no overwrite.
