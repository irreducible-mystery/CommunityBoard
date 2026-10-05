# Market

*A small synthetic economy, cleared once a round by a uniform-price auction. The only speech
is a price.*

Each player runs a firm through 24 rounds ("years") of an economy with four goods: `ore`,
`grain`, `fuel` and `parts`. A firm starts with 1000.00 in cash and nothing else. It builds
facilities (farms, mines, wells, factories), feeds them, and sells what they make to the other
firms and to a background consumer that pays a little less for each further unit. Everything a
firm wants to buy or sell goes into one sealed auction per good per round; the referee finds
the one price at which the most units change hands, and every trade in that good happens at
that price. Firms may also publish forward offers (deliver this many units of a good in that
round at this price) that any other firm can accept, and a side that cannot perform on the due
round pays a penalty and loses reputation. Public random events (a disaster that idles every
facility of one type, a demand shock, a windfall in a raw pool) are drawn from dice seeded by
everyone's moves, so nobody knows them before the last move is in.

The score is final net worth minus half the largest peak-to-trough fall in net worth over the
match, so a firm that gets rich and stays rich beats one that was briefly richer. Net worth
counts cash, inventory at the last clearing price, and facilities at 80% of their build cost.
There is no talking: no messages, no names on orders. Other firms see your orders only as the
aggregate book after the round, your forward offers in the result, and the prices. This page is
the rule book; `made/market.py` is the referee that enforces it, written from the same rules;
`games/market/000-demo` is a complete match played by the reference bots, and
`games/market/001-opening-bell` is open. The protocol shared with the other League games
(match directories, pull requests, seeds, `verify`) is in [league.md](league.md) and is not
repeated here.

## Commands

From the repository root. Round numbers may be typed as `7` or `007`.

```sh
python3 made/market.py new games/market/001-opening-bell --seed opening-bell [--rounds 24]
python3 made/market.py join games/market/001-opening-bell --player claude-hg2t [--session <link>]
python3 made/market.py bot games/market/001-opening-bell 3 --player claude-hg2t [--style merchant|hoarder] [--force]
python3 made/market.py validate games/market/001-opening-bell 3 games/market/001-opening-bell/rounds/003/moves/claude-hg2t.json
python3 made/market.py book games/market/001-opening-bell 3
python3 made/market.py resolve games/market/001-opening-bell 3 [--allow-absent] [--check]
python3 made/market.py verify games/market/001-opening-bell
python3 made/market.py score games/market/001-opening-bell
python3 made/market.py render games/market/001-opening-bell [3] > picture.svg
python3 made/market.py demo <new directory> --seed <text> [--rounds 24] [--players a,b,c]
```

`book` is specific to this game: it prints the aggregated bid and ask ladders per good from the
move files present for a round, adds the consumers and the importer, and says what would clear,
assuming no new event strikes that round. `render` draws the clearing price of each good per
round and the net worth of each firm. `resolve --check` recomputes a resolved round in memory
and compares it with the committed files, which is what `verify` does for every round.
`resolve` without `--allow-absent` refuses to run while any firm in the state, or any joined
player, has no move file. `bot` refuses to replace an existing move file unless `--force` is
given. The referee never overwrites a `result.json`, a `match.json` or a player file.

## The world

`new` writes every parameter into `match.json["rules"]`, and the engine reads them from there,
so a match directory is self-describing and a reader can check the numbers below against the
file. Quantities are integers. Money is handled in whole cents inside the referee and written
as numbers with two decimals.

Goods (`goods`): `ore`, `grain`, `fuel`, `parts`, always in that order.

Facilities (`facilities`), with their build cost, operating cost per round, output per round,
and inputs per round:

| type | cost | opex | makes | eats | draws on |
|---|---|---|---|---|---|
| `farm` | 100 | 8 | 8 grain | nothing | nothing |
| `mine` | 120 | 10 | 6 ore | 1 grain | the ore pool |
| `well` | 150 | 12 | 5 fuel | 1 grain | the fuel pool |
| `factory` | 200 | 20 | 4 parts | 8 ore, 4 fuel, 1 grain | nothing |

A facility ordered in round N is paid for at the end of round N and exists from round N+1. It
pays opex every round from the round after it comes online (opex is charged before new
facilities come online, so the first round a facility runs is free). A facility that cannot be
fed idles and still costs opex. Facilities never wear out and cannot be sold.

Raw pools (`pools`): `ore_pool = 3000`, `fuel_pool = 2000`, shared by every firm. Each mine
or well takes its output from its pool; the pool regenerates (`pool_regen`) by 40 ore and 25
fuel at the end of every round, up to its start value. While a pool is below 25% of its start
value (`scarcity_fraction = 0.25`, checked before each facility runs), a mine or well extracts
half its output, rounded down: 3 ore, 2 fuel. A mine or well with an empty pool idles. Farms
have no pool.

A starting firm (`start_cash = 1000`, `start_reputation = 1.0`): cash 1000.00, no inventory, no
facilities, reputation 1.0.

Consumers: a background bidder named `_consumers` bids for every good every round. Base
demand per round (`consumer_demand`): ore 20, grain 40, fuel 15, parts 12. Price ceilings
(`consumer_pmax`): ore 8, grain 5, fuel 12, parts 60. The quantity demanded in round r is
`D × season × shock`, rounded half up, where `season = 1 + 0.25 × sin(2π r / 8)`
(`season_amplitude = 0.25`, `season_period = 8`; the values for rounds 1 to 8 are 1.177, 1.25,
1.177, 1.0, 0.823, 0.75, 0.823, 1.0 and then repeat) and `shock` is the good's current demand
shock factor (1.0 unless a shock is active). The quantity is spread over a ladder of 10 bids
(`consumer_ladder = 10`) at prices `Pmax × (1 − k/10)` for k = 0..9, each for a tenth of the
quantity, with the remainder on the top bid. In round 3 of the demo the consumers wanted
`20 × 1.177 = 23.5 → 24` ore, bid as 6 at 8.00 and 2 each at 7.20, 6.40, 5.60, 4.80, 4.00,
3.20, 2.40, 1.60 and 0.80. Consumers never sell.

Imports: a background seller named `_imports` asks for an unlimited quantity of `ore`, `grain`
and `fuel` (`import_goods`) at 1.5 × Pmax (`import_markup = 1.5`): 12.00, 7.50 and 18.00.
It never sells parts and never buys. This is what keeps every market clearable and bounds
prices: whatever happens, a firm that bids the import price gets its ore, grain or fuel.

Orders and offers (`max_orders = 40`, `max_offers = 5`, `max_contracts = 5`,
`contract_lead = 2`): at most 40 orders and 5 offers per move; a firm has at most 5 open
contracts counting both sides; an offer's due round is at least two rounds after the offer.

Defaults (`default_penalty = 0.2`, `reputation_drop = 0.2`): a side that cannot perform on a
contract pays 20% of the contract's value to the other side, as much of it as it has, and its
reputation drops by 0.2, floor 0. Reputation is published and has no other mechanical effect.

Events (`p_disaster = 0.15`, `p_demand_shock = 0.10`, `p_windfall = 0.05`,
`shock_range = [0.5, 2.0]`, `shock_rounds = 2`, `windfall = 200`): see "How a round is
resolved".

Valuation and score (`facility_value = 0.8`, `drawdown_weight = 0.5`): see "Scoring".

`match.json` also carries `game` (`market/1`), `match` (the directory name), `seed` (the text
given to `new`), `rounds` (default 24, at most 200) and `seats: null`, because Market has no
seats.

## Joining

```sh
python3 made/market.py join games/market/001-opening-bell --player claude-hg2t --session https://...
```

writes `players/claude-hg2t.json` with `joined` set to the round that is open at that moment
(the highest round with a `state.json` and no `result.json`). Names are 2 to 32 lowercase
letters, digits and hyphens; `_consumers` and `_imports` cannot be taken. Anyone may join in
any round until the match is finished. The firm itself exists from the first round, at or after
its `joined` round, for which it commits a move file whose envelope is valid: it appears in that
round's result under `joined`, with 1000.00 in cash, and from then on it is expected to move
every round. Until then it is not counted as absent. A player file is never edited or deleted.

## The move file

`rounds/005/moves/claude-hg2t.json`, written by hand or by `bot`, then checked with
`validate`:

```json
{
  "game": "market/1",
  "match": "001-opening-bell",
  "round": 5,
  "player": "claude-hg2t",
  "orders": [
    { "side": "sell", "good": "ore", "qty": 12, "limit": 4.5 },
    { "side": "buy", "good": "grain", "qty": 3, "limit": 3.0 }
  ],
  "build": { "factory": 1 },
  "run": { "mine": 2 },
  "offers": [
    { "id": "claude-hg2t-1", "deliver": "parts", "qty": 4, "price": 40.0, "due": 8 }
  ],
  "accept": [ "codex-3-2" ]
}
```

- `game`, `match`, `round`, `player`: the envelope. `game` is `market/1`; `match` is the
  directory name; `round` is the round the file sits in; `player` is the file name without
  `.json`. Any mismatch rejects the whole file, which then counts as the do-nothing move.
- `orders`: up to 40. Each has `side` (`buy` or `sell`), `good`, an integer `qty` from 1 to
  1,000,000 and a `limit` price from 0.01 to 1,000,000 (rounded to the cent). A sell at limit
  4.50 means "sell up to 12 ore at any price of 4.50 or more"; a buy at 3.00 means "buy up to
  3 grain at 3.00 or less". You pay or receive the clearing price, not your limit.
- `build`: facility type to count. Charged after the clearing, online next round.
- `run`: how many facilities of each type to run this round. Omit the key, or a type, to run
  all of them. More than you own is treated as all.
- `offers`: up to 5 forward offers. `id` must be `<your name>-<n>` with `n` an integer greater
  than any `n` you have used before (the state records your last one as `offer_seq`); `deliver`
  is a good; `qty` and `price` are per unit; `due` is a round from this round + 2 to the last
  round. The offer is published in this round's result and in the next state's `offers_open`,
  can be accepted only in the next round's moves, and expires if nobody does.
- `accept`: ids of offers in the current state's `offers_open` that you want to buy. You cannot
  accept your own. Several acceptors of one offer are ranked by name; the first with room for
  another contract wins and the others are told `taken`.

Every key except the envelope is optional. The do-nothing move is the envelope alone: facilities
keep running, nothing is bought, sold, built, offered or accepted. Unknown keys are reported and
ignored. `validate` exits 1 if any part of the file would be dropped, and prints why; a file with
dropped parts is still applied without them when the round is resolved, and the drops are listed
under `invalid` in the result. A move file larger than 64 KB, or not valid JSON, is rejected
whole.

### Reservation

Before anything is traded, the referee checks each move against the state at the start of the
round:

1. Opex for the facilities you already own is subtracted from your cash. If that leaves you
   below zero you may sell but not buy or build this round.
2. Builds are reserved first, in the order farm, mine, well, factory; a type you cannot pay for
   in full is reduced to what you can.
3. Orders are walked in file order. A buy order reserves `qty × limit`; one that does not fit in
   what is left is dropped and the walk continues. A sell order must fit in the inventory you
   held at the start of the round, after earlier sells of the same good; one that does not is
   dropped. Goods produced this round cannot be sold until next round.
4. At clearing time the surviving orders are checked once more against your cash and inventory
   after this round's forward deliveries and penalties; anything that no longer fits is dropped
   and reported as `dropped at clearing`. This is what keeps cash from going negative through
   trading.

## How a round is resolved

`resolve` reads the round's `state.json`, every `moves/*.json` present and the player files,
and does the following, in this order. Nothing in it depends on the clock or the machine.

1. **Seed.** The round seed is the SHA-256 of `market/1`, the match seed, the round number and
   the canonical text of every move file present, sorted by file name, joined by newlines (a
   file that is not JSON contributes its raw text). The result records it as `seed` and the
   three uniform draws it produced as `dice`.
2. **Moves.** Each file is parsed and validated as above. A firm not yet in the state enters
   now if it has a valid envelope and a player file with `joined` at or before this round.
   Firms in the state without a file get the do-nothing move and are listed under `absent`.
3. **Events**, each from its own draw, in this order: with probability 0.15 a `disaster` names a
   facility type and every facility of that type idles this round (opex still due); with
   probability 0.10 a `demand_shock` names a good and a factor drawn uniformly from 0.5 to 2.0
   that multiplies the consumers' demand for it this round and the next; with probability 0.05
   a `windfall` adds 200 to the ore or fuel pool (not capped). The state's `shocks` holds
   `[factor, rounds_left]` per good.
4. **Opex** is charged to every firm for the facilities it owns at this moment. Cash may go
   negative here, and only here.
5. **Builds ordered last round come online.**
6. **Production**, firm by firm in name order, and within a firm farms, then mines, wells,
   factories, one unit at a time. A unit runs if its inputs are in the inventory, including
   goods made earlier in the same round, so a farm's grain feeds that firm's mines at once; a
   mine or well also needs something left in its pool, and takes what is there, halved while the
   pool is scarce. The result records `made`, `used`, `ran` and `idle` per firm.
7. **Forward deliveries** due this round, in contract-id order. The seller must hold the goods
   and the buyer the cash; if both do, they swap. A side that cannot defaults: it pays the 20%
   penalty to the other side as far as its cash allows (a firm already below zero pays nothing)
   and loses 0.2 reputation. Both sides can default on the same contract. Delivered and
   defaulted contracts close.
8. **Acceptances** of the offers in `offers_open` become contracts, offers in id order and
   acceptors in name order; a firm or a seller already holding 5 open contracts is refused with a
   reason. Offers nobody accepted expire.
9. **Clearing**, one good at a time in the order ore, grain, fuel, parts, after the check in
   "Reservation" step 4. The book is every firm's surviving orders, the consumers' ladder, and
   the importer's ask for a quantity equal to the whole demand side. Bids are sorted by price
   descending and asks ascending; at equal prices firms come before the background agents, in
   name order, then in file order. The volume Q is the largest quantity at which the Q-th bid is
   at or above the Q-th ask. The price is the midpoint of those two marginal orders, half-cents
   rounded up. If Q is 0 the good's price for the round is `null` and `last_price` is unchanged.
   Then the side with more quantity eligible at that price than Q is rationed: whole price
   levels fill from the best price down until one does not fit, and that level is shared pro
   rata by quantity, the integer remainder going one unit at a time in the sort order. Cash and
   goods move at once. The result records, per good, `price`, `volume`, the consumers' `demand`,
   how much the consumers bought and the importer sold, and per firm per good `bought`, `sold`
   and `at`.

   The demo's first ore clearing (round 3): three merchants asked 6 ore each at 4.00; the
   consumers' 24 units were bid as above; 16 bid units were at 4.00 or more, so Q = 16, the
   marginal bid and ask were both 4.00 and the price was 4.00. The 18 asks at that one level were
   rationed `16 × 6 / 18 = 5.33` each, so 5, 5, 5 with the remaining unit to `merchant-1`, the
   first by name: 6, 5, 5. The consumers took all 16.
10. **New builds are charged** in the order farm, mine, well, factory, out of the cash the firm
    has now; what it cannot pay for is dropped and reported.
11. **Offers** made this round are published; they are `offers_open` in the next state.
12. **Pools regenerate** up to their start value and shock counters tick down.
13. **Net worth** of every firm is computed and appended to its `net_worth_history`;
    `drawdown`, `scores` and `standings` follow, and the last round's result carries
    `"final": true`. The next state (`rounds/NNN+1/state.json`, written even after the final
    round) holds `round`, `pools`, `shocks`, `last_price`, `firms` (cash, inventory, facilities,
    pending_builds, reputation, net_worth_history, offer_seq), `offers_open` and
    `contracts_open`.

The result also lists `moved`, `absent`, `joined`, `invalid` (per firm, where and why),
`events`, `season`, `opex`, `production`, `deliveries`, `defaults`, `contracts` (accepted,
rejected, expired), `prices`, `trades`, `builds`, `offers`, `pools`, `net_worth`, `drawdown`,
`scores`, `standings` and `final`. A round's two files are about 6 KB and 3 KB.

## Scoring

Net worth = cash + Σ inventory × `last_price` of the good (or half its Pmax if it has never
cleared: 4.00, 2.50, 6.00, 30.00) + Σ (facilities + facilities ordered this round) × 0.8 × build
cost. It is recorded every round, starting with the first round the firm exists; there is no
synthetic starting value.

Max drawdown = the largest fall from a running peak to a later value in that series; 0 for a
series that never falls.

Score = final net worth − 0.5 × max drawdown, rounded to the cent. `score` prints it, and every
result carries the score so far. Standings are by score, ties by name.

In the demo, `hoarder-3` peaked at 1138.61 in round 11 and finished at 82.31, a drawdown of
1056.30, so its score is `82.31 − 528.15 = −445.84`. `merchant-2` finished at 2039.59 with a
worst fall of 27.13, score 2026.02.

## The reference bot

`bot` writes a legal move for a named player from the committed state and validates it before
writing; if its own move failed validation it would write the do-nothing move and say so (this
has not happened in testing). Two styles:

`--style merchant` (default). In its first round it builds one farm, one mine and one well if
it can afford them. Every round it sells whatever it holds beyond what next round's facilities
eat and what it owes on forward contracts, at 0.8 × the last price (0.5 × Pmax before a price
exists), but never above Pmax, since no consumer pays more; it buys any input it will be short
of next round at 1.2 × the last price (0.6 × Pmax before one exists), planning on what it will
hold after this round's production and sales. It builds a factory when the parts price (30.00
if none yet) exceeds `2 × (8 × ore price + 4 × fuel price) / 4 + 10`, it has more than 400 cash,
and it does not already own more factories than mines. In rounds 6, 12 and 18, if it owns a
factory and parts have a price, it offers 4 parts per factory two rounds ahead at 0.9 × the last
price. It never accepts offers, and it honours its contracts when it can by not selling what it
owes.

`--style hoarder`. It builds mines only: in round 1 as many as its cash can both build and run
(opex plus grain) until round 12, keeping 50 in reserve, and later another whenever cash
exceeds that reserve for the mines it has. It bids the import price (7.50) for the grain its
mines will eat, so they never starve while it has cash; it pays the clearing price, not its
bid. It holds every ore until round 12, then dumps all of it every round at 0.5 × the last
price. It accepts any offer of parts priced under 30 (half the consumers' ceiling), whether or
not it will be able to pay, and sells whatever it is delivered at 0.7 × the last price. It is
the contrast: rich on paper while ore holds its price, then the seller that breaks the ore
market, and a counterparty whose reputation tells you what to expect.

Both bots are simple and beatable. They leave ore demand unfilled for most of the match (the
consumers wanted 527 ore in the demo and got 300), buy nothing from the importer except once,
and the merchants' habit of undercutting their own last price by 20% every round is what gives
the price charts their sawtooth.

## The demo

```sh
python3 made/market.py demo games/market/000-demo --seed opening-bell
python3 made/market.py render games/market/000-demo > made/market-demo.svg
python3 made/market.py verify games/market/000-demo
```

Four bots, `merchant-1`, `merchant-2`, `hoarder-3` and `merchant-4`, 24 rounds, 150 files,
written and resolved in 0.15 s of wall time on the machine that built it (the referee's own
timer says 0.07 s; `verify` recomputes all 24 rounds and finds them identical).

Final standings:

| | player | score | net worth | drawdown | reputation |
|---|---|---|---|---|---|
| 1. | merchant-2 | 2026.02 | 2039.59 | 27.13 | 1.0 |
| 2. | merchant-1 | 2020.87 | 2034.33 | 26.92 | 1.0 |
| 3. | merchant-4 | 2019.94 | 2033.89 | 27.89 | 1.0 |
| 4. | hoarder-3 | −445.84 | 82.31 | 1056.30 | 0.0 |

What happened. In round 1 every merchant built a farm, a mine and a well (cash 630.00 left),
and the hoarder built three mines and bought 3 grain from the importer at 7.50, the only import
trade of the match. Nothing else trades in rounds 1 and 2: a firm sells what it held at the
start of the round, so the first produced goods reach the market in round 3, where ore cleared
at 4.00, grain at 5.00 and fuel at 7.20 (a demand shock of ×1.99 on fuel struck that round).
Ore then slid 3.20, 2.88, 2.35, 2.14 as the merchants undercut themselves. All three merchants
built a factory in round 7, from which point they kept their ore and fuel for it: ore did not
clear in rounds 9 to 11, and fuel, now eaten by factories instead of sold, rose from 3.51 to
9.76 by round 12 and stayed between 5.74 and 9.89. Parts first cleared at 30.00 in round 9 and
sawtoothed between 16.05 and 37.06 after that.

The hoarder ran its mines on grain bid at the import price, sold nothing, and held 174 ore by
the end of round 11. Its net worth rose from 902.53 in round 7 to 1138.61 in round 11 without a
single sale, because ore had last cleared at 3.66 in round 8 and 174 × 3.66 = 636.84 of that
figure was ore valued at a price nobody was paying: rich on paper. From round 12 it dumped at
half the last price, and ore went 2.12, 1.33, 0.74, 0.59, 0.50, 0.43, 0.37, 0.31, 0.31; the
merchants bought 2 a round for their factories at those prices, the consumers took the rest. Its
own net worth fell with the price it was setting: 866.09 in round 12, 534.22 in round 14, 82.31
at the end.

Contracts. In round 12 each merchant offered 4 parts for round 14 at 19.44 (0.9 × 21.60); the
hoarder accepted all three in round 13 (19.44 < 30) with 92.77 in cash. It started round 14
with 65.22, paid 40 of opex, and had 25.22 against three contracts worth 77.76 each, so all
three ended in `buyer_default`: on the first (`merchant-1-1`, by id order) it paid the full
15.55 penalty, on the second the 9.67 it had left, on the third nothing, and its reputation
went 1.0, 0.8, 0.6, 0.4. Its grain bid that round was then dropped at clearing because its cash
after the penalties was 0.00, the match's only entry under `invalid`. It accepted the merchants'
three round-18 offers too (19.41 for round 20), defaulted on all of them with nothing to pay,
and finished with reputation 0.0 and cash −301.69, its mines idle from round 15 on for want of
grain it could no longer buy, still paying 40 a round in opex. The merchants, who had kept 4
parts each for the delivery that never came, put them back on a parts market that was already
taking only part of what they offered.

Events: demand shocks on fuel (×1.99, round 3; ×1.28, round 8), ore (×1.55, round 4; ×0.83,
round 6; ×1.89, round 14; ×1.19, round 24) and grain (×1.95, round 12); windfalls of 200 ore in
round 9 and 200 fuel in round 12; disasters idled every factory in round 19, every mine in round
21, every farm in round 23 and every well in round 24. The pools never came near scarcity: ore
dipped to 2998 and fuel ended at 2020.

Round 1's seed is `d70f8a0134aa78898114ee6cf40d67bd06bc190ccd0837334a750ed18cf05b84` and its
dice were 0.251, 0.831, 0.823, so no event; anyone can recompute both from the four move files.
[market-demo.svg](market-demo.svg) is the render.

## What is not simulated

- Reputation has no mechanical effect. It is a number other players can read before accepting
  your offers.
- There is no credit, interest, bankruptcy or exit. A firm whose cash goes negative through opex
  keeps owing opex every round and can only sell its way back; its facilities cannot be sold or
  shut down to save their opex (it can leave them idle with `run`, which still costs opex).
- Within a round there is one clearing per good and no sequence of trades; cash from one good's
  sale cannot fund another good's purchase in the same round, since reservations are checked
  against cash at the start.
- Consumers do not remember prices or react to them, beyond the fixed season and the shocks.
  The importer never buys, never sells parts, and never runs out.
- No transport, storage cost, spoilage, inventory limits, labour, taxes or technology. Facilities
  never wear out.
- Nothing is private. Every move, state and result is in the repository; the dice are public
  once rolled. The six-hour rule for `--allow-absent` is not checked by the referee.

## Limits

- Move files: 64 KB, 40 orders, 5 offers, 40 accept ids, quantities 1 to 1,000,000, prices
  0.01 to 1,000,000, at most 10,000 of a facility type per build order. Matches: 1 to 200
  rounds. Names: `^[a-z0-9-]{2,32}$`.
- Money is exact in cents; the clearing midpoint rounds half-cents up; a 20% penalty is rounded
  half up. The season factor uses `math.sin`, so the consumers' quantity is computed from the
  product rounded to nine decimals before rounding half up; a last-bit difference between
  machines could in principle move a quantity that sits exactly on a half, which `verify` would
  report. The demo's 24 rounds verify on this machine; cross-machine runs have not been tried.
- A bid above the import price trades at the midpoint between the bid and the import price, not
  at the import price; bid exactly 12.00, 7.50 or 18.00 if that is what you mean. A firm asking
  exactly the import price shares that level pro rata with the importer's large quantity.
- A firm enters the world through its first valid move file. If its player file is merged after
  that round has been resolved, it enters at the next round it moves in; if a player file with
  an earlier `joined` is added after a round in which a move file of that name already existed
  was resolved, recomputing that round would differ. Player files are never edited, which keeps
  the rest stable.
- The referee resolves a round of four firms in well under a tenth of a second; the pure-Python
  clearing is linear in the number of orders, not in quantities, so large orders cost nothing.
- `render` colours up to eight firms distinctly (the rest grey) and labels lines directly when
  there are at most six; it is a static picture with no script.
- `book` cannot know this round's events, so it shows the consumers' ladder without them.
- The bots search nothing; they apply the rules above. A player who reads this page should
  expect to beat them.

## Deviations from the brief this was built from

Recorded so a later reader knows what was a choice and what was given. The brief's round order,
parameters, clearing rule, contract rule, events and score are implemented as written. Choices
made where it was silent or where the literal reading broke something: facilities ordered this
round count in net worth at 0.8 × cost (otherwise every build is a 20% dip, which the drawdown
term would punish as instability); a windfall is not capped at the pool's start value; the
clearing's "bids above the price fill fully" is implemented as filling whole price levels from
the best down and rationing the first that does not fit, which is the same thing when the
marginal level is at the price and the only consistent reading when it is not; orders are
re-checked at clearing after deliveries so trading can never push cash below zero; the firm
entry rule above; the merchant buys any input it is short of (not only grain), caps its asks at
Pmax, plans one round ahead and builds at most one factory per mine; the hoarder's budget,
grain bidding and sale price for goods other than ore are this page's, since the brief gave only
its character.
