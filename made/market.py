#!/usr/bin/env python3
"""Market: the League's economy referee (game version market/1).

Four goods, four kinds of facility, one uniform-price double auction per round, forward
contracts, public random shocks, and a score that rewards final net worth minus half the
worst drawdown. The protocol every League game shares is in made/league.md; the rules of
this game, with the demo's real numbers, are in made/market.md.

Usage, from the repository root:

  python3 made/market.py new games/market/001-opening-bell --seed opening-bell [--rounds 24]
  python3 made/market.py join games/market/001-opening-bell --player claude-hg2t [--session <link>]
  python3 made/market.py bot games/market/001-opening-bell 3 --player claude-hg2t [--style merchant|hoarder]
  python3 made/market.py validate games/market/001-opening-bell 3 <move-file.json>
  python3 made/market.py book games/market/001-opening-bell 3
  python3 made/market.py resolve games/market/001-opening-bell 3 [--allow-absent] [--check]
  python3 made/market.py verify games/market/001-opening-bell
  python3 made/market.py score games/market/001-opening-bell
  python3 made/market.py render games/market/001-opening-bell [3] > picture.svg
  python3 made/market.py demo games/market/000-demo --seed opening-bell [--rounds 24]

Standard library only. The simulation is a set of pure functions over plain dicts
(initial_state, validate_move, resolve_round, clear, run_production, max_drawdown); the
commands are a thin layer that reads and writes the match directory. Money is handled in
integer cents inside the engine and written as floats with two decimals.
"""
import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
from pathlib import Path

VERSION = "market/1"
NAME_RE = re.compile(r"^[a-z0-9-]{2,32}$")
CONSUMERS = "_consumers"
IMPORTS = "_imports"
TOLERANCE = 1e-8
MAX_MOVE_BYTES = 65536
MAX_QTY = 1000000
MAX_PRICE = 1000000.0
MAX_BUILD = 10000
MAX_ACCEPTS = 40
MOVE_KEYS = ("game", "match", "round", "player", "orders", "build", "run", "offers", "accept")


def default_rules():
    """The world as `new` writes it into match.json["rules"]. The engine reads only this."""
    return {
        "goods": ["ore", "grain", "fuel", "parts"],
        "facilities": {
            "farm": {"cost": 100, "opex": 8, "output": {"grain": 8}, "inputs": {}, "pool": None},
            "mine": {"cost": 120, "opex": 10, "output": {"ore": 6}, "inputs": {"grain": 1}, "pool": "ore"},
            "well": {"cost": 150, "opex": 12, "output": {"fuel": 5}, "inputs": {"grain": 1}, "pool": "fuel"},
            "factory": {"cost": 200, "opex": 20, "output": {"parts": 4},
                        "inputs": {"ore": 8, "fuel": 4, "grain": 1}, "pool": None},
        },
        "run_order": ["farm", "mine", "well", "factory"],
        "pools": {"ore": 3000, "fuel": 2000},
        "pool_regen": {"ore": 40, "fuel": 25},
        "scarcity_fraction": 0.25,
        "start_cash": 1000,
        "start_reputation": 1.0,
        "consumer_demand": {"ore": 20, "grain": 40, "fuel": 15, "parts": 12},
        "consumer_pmax": {"ore": 8, "grain": 5, "fuel": 12, "parts": 60},
        "consumer_ladder": 10,
        "season_amplitude": 0.25,
        "season_period": 8,
        "import_goods": ["ore", "grain", "fuel"],
        "import_markup": 1.5,
        "max_orders": 40,
        "max_offers": 5,
        "max_contracts": 5,
        "contract_lead": 2,
        "default_penalty": 0.2,
        "reputation_drop": 0.2,
        "p_disaster": 0.15,
        "p_demand_shock": 0.10,
        "p_windfall": 0.05,
        "shock_range": [0.5, 2.0],
        "shock_rounds": 2,
        "windfall": 200,
        "facility_value": 0.8,
        "drawdown_weight": 0.5,
    }


# ----------------------------------------------------------------------------- helpers

def dumps(obj):
    """Canonical JSON, the format of every file the referee writes."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def canonical_text(text):
    """The text of a move file as it enters the round seed: canonical JSON if it parses, raw otherwise."""
    try:
        return json.dumps(json.loads(text), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    except Exception:
        return text


def round_seed(match_seed, rnd, move_texts):
    """SHA-256 of version, match seed, round number and every move file present, sorted by player."""
    parts = [VERSION, match_seed, str(rnd)]
    parts += [canonical_text(move_texts[name]) for name in sorted(move_texts)]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def cents(x):
    return int(round(x * 100))


def money(c):
    return round(c / 100, 9)


def copy_json(obj):
    return json.loads(json.dumps(obj))


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def half_up(x):
    return int(math.floor(x + 0.5))


def season_factor(rules, rnd):
    return 1 + rules["season_amplitude"] * math.sin(2 * math.pi * rnd / rules["season_period"])


def new_firm(rules):
    return {
        "cash": money(cents(rules["start_cash"])),
        "inventory": {g: 0 for g in rules["goods"]},
        "facilities": {t: 0 for t in rules["facilities"]},
        "pending_builds": {t: 0 for t in rules["facilities"]},
        "reputation": rules["start_reputation"],
        "net_worth_history": [],
        "offer_seq": 0,
    }


def nothing_move():
    """The do-nothing move: facilities keep running, nothing is traded, built, offered or accepted."""
    return {"orders": [], "build": {}, "run": None, "offers": [], "accept": []}


def initial_state(match):
    rules = match["rules"]
    return {
        "game": VERSION,
        "match": match["match"],
        "round": 1,
        "pools": dict(rules["pools"]),
        "shocks": {g: [1.0, 0] for g in rules["goods"]},
        "last_price": {g: None for g in rules["goods"]},
        "firms": {},
        "offers_open": [],
        "contracts_open": [],
    }


def eligible(players, name, rnd):
    p = players.get(name)
    return p is not None and is_int(p.get("joined")) and p["joined"] <= rnd


# ----------------------------------------------------------------------------- the book

def consumer_bids(rules, rnd, shocks, good):
    """The background consumer's bid ladder for one good: (orders, quantity, season)."""
    demand = rules["consumer_demand"][good]
    pmax = cents(rules["consumer_pmax"][good])
    season = season_factor(rules, rnd)
    shock = shocks.get(good, [1.0, 0])[0]
    qty = half_up(round(demand * season * shock, 9))
    steps = rules["consumer_ladder"]
    base, rem = divmod(qty, steps)
    orders = []
    for k in range(steps):
        q = base + (rem if k == 0 else 0)
        price = pmax * (steps - k) // steps
        if q > 0 and price > 0:
            orders.append({"owner": CONSUMERS, "side": "buy", "good": good, "qty": q, "price": price, "seq": k})
    return orders, qty, season


def import_price(rules, good):
    return int(round(rules["consumer_pmax"][good] * rules["import_markup"] * 100))


def market_import_price(rules, good):
    """The importer's price of a good in currency, as a player would write it as a limit."""
    return import_price(rules, good) / 100


def import_ask(rules, good, qty):
    """The importer's ask: unlimited in effect, so its quantity is the whole demand side."""
    if good not in rules["import_goods"] or qty <= 0:
        return None
    return {"owner": IMPORTS, "side": "sell", "good": good, "qty": qty, "price": import_price(rules, good), "seq": 0}


def _background(order):
    return 1 if order["owner"] in (CONSUMERS, IMPORTS) else 0


def allocate(orders, quantity):
    """Fill `orders` (best price first) up to `quantity`. Whole price levels fill fully; the
    first level that does not fit is rationed pro rata by quantity, the integer remainder
    going one unit at a time in the list's order (player name, background agents last)."""
    fills = []
    left = quantity
    k = 0
    while k < len(orders) and left > 0:
        end = k + 1
        while end < len(orders) and orders[end]["price"] == orders[k]["price"]:
            end += 1
        level = orders[k:end]
        total = sum(o["qty"] for o in level)
        if total <= left:
            fills += [(o, o["qty"]) for o in level]
            left -= total
        else:
            shares = [o["qty"] * left // total for o in level]
            rem = left - sum(shares)
            for i in range(len(level)):
                if rem <= 0:
                    break
                shares[i] += 1
                rem -= 1
            fills += [(o, s) for o, s in zip(level, shares) if s > 0]
            left = 0
        k = end
    return fills


def clear(bids, asks):
    """Uniform-price clearing of one good.

    Orders are dicts with owner, qty, price (integer cents) and seq (file order). Bids are
    sorted by price descending, asks ascending; ties put background agents last, then player
    name, then file order. The volume is the largest Q at which the Q-th bid is at or above
    the Q-th ask; the price is the midpoint of those two marginal orders, half-cents rounded
    up. Returns {"price": cents or None, "volume": Q, "fills": [(order, qty), ...]}.
    """
    bids = sorted(bids, key=lambda o: (-o["price"], _background(o), o["owner"], o["seq"]))
    asks = sorted(asks, key=lambda o: (o["price"], _background(o), o["owner"], o["seq"]))
    i = j = 0
    bi = aj = 0
    volume = 0
    marginal_bid = marginal_ask = None
    while i < len(bids) and j < len(asks) and bids[i]["price"] >= asks[j]["price"]:
        take = min(bids[i]["qty"] - bi, asks[j]["qty"] - aj)
        volume += take
        marginal_bid, marginal_ask = bids[i]["price"], asks[j]["price"]
        bi += take
        aj += take
        if bi == bids[i]["qty"]:
            i += 1
            bi = 0
        if aj == asks[j]["qty"]:
            j += 1
            aj = 0
    if volume == 0:
        return {"price": None, "volume": 0, "fills": []}
    price = (marginal_bid + marginal_ask + 1) // 2
    fills = allocate([o for o in bids if o["price"] >= price], volume)
    fills += allocate([o for o in asks if o["price"] <= price], volume)
    return {"price": price, "volume": volume, "fills": fills}


# ----------------------------------------------------------------------------- moves

def parse_move(text):
    """Move file text to (object, problem). The object is None when the file is unusable."""
    if len(text.encode("utf-8")) > MAX_MOVE_BYTES:
        return None, "file larger than %d bytes" % MAX_MOVE_BYTES
    try:
        return json.loads(text), None
    except Exception:
        return None, "not valid JSON"


def validate_move(match, state, rnd, name, obj, players=None):
    """Check one parsed move against the state at the start of round `rnd`.

    Returns (clean, problems, fatal). `clean` is the normalised move the engine applies
    (prices in cents, dropped parts removed); `problems` is a list of {"where", "reason"};
    `fatal` means the whole file was rejected and `clean` is the do-nothing move. When
    `players` (name -> player file) is given, a firm not yet in the state must have a player
    file with joined <= rnd.
    """
    rules = match["rules"]
    goods = rules["goods"]
    facs = rules["facilities"]
    problems = []
    clean = nothing_move()

    def bad(where, reason):
        problems.append({"where": where, "reason": reason})

    if not isinstance(name, str) or not NAME_RE.match(name):
        bad("file", "player name must match ^[a-z0-9-]{2,32}$")
        return clean, problems, True
    if not isinstance(obj, dict):
        bad("file", "a move must be a JSON object")
        return clean, problems, True
    if obj.get("game") != VERSION:
        bad("game", "must be %r" % VERSION)
    if obj.get("match") != match["match"]:
        bad("match", "must be %r" % match["match"])
    if not is_int(obj.get("round")) or obj.get("round") != rnd:
        bad("round", "must be %d" % rnd)
    if obj.get("player") != name:
        bad("player", "must equal the file name, %r" % name)
    if problems:
        return clean, problems, True
    firm = state["firms"].get(name)
    if firm is None:
        if players is not None and not eligible(players, name, rnd):
            bad("player", "no players/%s.json with joined <= %d" % (name, rnd))
            return clean, problems, True
        firm = new_firm(rules)
    for key in sorted(obj):
        if key not in MOVE_KEYS:
            bad(key, "unknown key, ignored")

    orders = obj.get("orders", [])
    if not isinstance(orders, list):
        bad("orders", "must be a list")
        orders = []
    if len(orders) > rules["max_orders"]:
        bad("orders", "more than %d orders; the rest are dropped" % rules["max_orders"])
        orders = orders[:rules["max_orders"]]
    parsed = []
    for i, o in enumerate(orders):
        where = "orders[%d]" % i
        if not isinstance(o, dict):
            bad(where, "must be an object")
            continue
        side, good, qty, limit = o.get("side"), o.get("good"), o.get("qty"), o.get("limit")
        if side not in ("buy", "sell"):
            bad(where, "side must be \"buy\" or \"sell\"")
            continue
        if good not in goods:
            bad(where, "good must be one of %s" % ", ".join(goods))
            continue
        if not is_int(qty) or qty < 1 or qty > MAX_QTY:
            bad(where, "qty must be an integer from 1 to %d" % MAX_QTY)
            continue
        if not is_num(limit) or limit <= 0 or limit > MAX_PRICE or cents(limit) < 1:
            bad(where, "limit must be a number from 0.01 to %d" % int(MAX_PRICE))
            continue
        parsed.append({"owner": name, "side": side, "good": good, "qty": qty, "price": cents(limit), "seq": i})

    build = obj.get("build", {})
    if not isinstance(build, dict):
        bad("build", "must be an object")
        build = {}
    clean_build = {}
    for t in sorted(build):
        n = build[t]
        if t not in facs:
            bad("build.%s" % t, "unknown facility type")
        elif not is_int(n) or n < 0 or n > MAX_BUILD:
            bad("build.%s" % t, "must be an integer from 0 to %d" % MAX_BUILD)
        elif n > 0:
            clean_build[t] = n

    run = obj.get("run", None)
    clean_run = None
    if run is not None:
        if not isinstance(run, dict):
            bad("run", "must be an object")
        else:
            clean_run = {}
            for t in sorted(run):
                n = run[t]
                if t not in facs:
                    bad("run.%s" % t, "unknown facility type")
                elif not is_int(n) or n < 0:
                    bad("run.%s" % t, "must be a non-negative integer; all of them will run")
                else:
                    clean_run[t] = n

    offers = obj.get("offers", [])
    if not isinstance(offers, list):
        bad("offers", "must be a list")
        offers = []
    if len(offers) > rules["max_offers"]:
        bad("offers", "more than %d offers; the rest are dropped" % rules["max_offers"])
        offers = offers[:rules["max_offers"]]
    seq = firm.get("offer_seq", 0)
    lead = rules["contract_lead"]
    for i, of in enumerate(offers):
        where = "offers[%d]" % i
        if not isinstance(of, dict):
            bad(where, "must be an object")
            continue
        oid = of.get("id")
        m = re.fullmatch(re.escape(name) + r"-([1-9][0-9]{0,8})", oid) if isinstance(oid, str) else None
        if not m:
            bad(where, "id must be \"%s-<n>\" with n a positive integer" % name)
            continue
        n = int(m.group(1))
        if n <= seq:
            bad(where, "id number must be greater than %d, the last this firm used" % seq)
            continue
        deliver, qty, price, due = of.get("deliver"), of.get("qty"), of.get("price"), of.get("due")
        if deliver not in goods:
            bad(where, "deliver must be one of %s" % ", ".join(goods))
            continue
        if not is_int(qty) or qty < 1 or qty > MAX_QTY:
            bad(where, "qty must be an integer from 1 to %d" % MAX_QTY)
            continue
        if not is_num(price) or price <= 0 or price > MAX_PRICE or cents(price) < 1:
            bad(where, "price must be a number from 0.01 to %d" % int(MAX_PRICE))
            continue
        if not is_int(due) or due < rnd + lead or due > match["rounds"]:
            bad(where, "due must be a round from %d to %d" % (rnd + lead, match["rounds"]))
            continue
        seq = n
        clean["offers"].append({"id": oid, "seller": name, "deliver": deliver, "qty": qty,
                                "price": money(cents(price)), "due": due})

    accept = obj.get("accept", [])
    if not isinstance(accept, list):
        bad("accept", "must be a list")
        accept = []
    if len(accept) > MAX_ACCEPTS:
        bad("accept", "more than %d ids; the rest are dropped" % MAX_ACCEPTS)
        accept = accept[:MAX_ACCEPTS]
    open_ids = {o["id"]: o for o in state["offers_open"]}
    seen = set()
    for i, oid in enumerate(accept):
        where = "accept[%d]" % i
        if not isinstance(oid, str):
            bad(where, "must be an offer id")
        elif oid in seen:
            bad(where, "duplicate")
        elif oid not in open_ids:
            bad(where, "no open offer %r" % oid)
        elif open_ids[oid]["seller"] == name:
            bad(where, "a firm cannot accept its own offer")
        else:
            seen.add(oid)
            clean["accept"].append(oid)

    # Reservation: builds first, then orders in file order, against cash after opex and
    # inventory at the start of the round.
    opex = sum(firm["facilities"].get(t, 0) * cents(facs[t]["opex"]) for t in facs)
    avail = cents(firm["cash"]) - opex
    negative = avail < 0
    if negative and clean_build:
        bad("build", "cash after opex is %.2f; a firm with negative cash cannot build" % money(avail))
        clean_build = {}
    if not negative:
        for t in rules["run_order"]:
            if t in clean_build:
                cost = cents(facs[t]["cost"])
                k = min(clean_build[t], avail // cost)
                if k < clean_build[t]:
                    bad("build.%s" % t, "only %d of %d affordable after opex and earlier builds" % (k, clean_build[t]))
                avail -= k * cost
                if k > 0:
                    clean_build[t] = k
                else:
                    del clean_build[t]
    kept = []
    sold = {g: 0 for g in goods}
    inventory = firm["inventory"]
    for o in parsed:
        where = "orders[%d]" % o["seq"]
        if o["side"] == "buy":
            exposure = o["qty"] * o["price"]
            if negative:
                bad(where, "cash after opex is %.2f; a firm with negative cash cannot buy" % money(avail))
                continue
            if exposure > avail:
                bad(where, "qty x limit = %.2f exceeds the %.2f left after opex, builds and earlier buys"
                    % (money(exposure), money(avail)))
                continue
            avail -= exposure
        else:
            held = inventory.get(o["good"], 0)
            if sold[o["good"]] + o["qty"] > held:
                bad(where, "sells %d %s but only %d held at the start of the round after earlier sells"
                    % (o["qty"], o["good"], held - sold[o["good"]]))
                continue
            sold[o["good"]] += o["qty"]
        kept.append(o)
    clean["orders"] = kept
    clean["build"] = clean_build
    clean["run"] = clean_run
    return clean, problems, False


# ----------------------------------------------------------------------------- the round

def run_production(rules, firm, inventory, run_plan, pools, disaster):
    """Run one firm's facilities in rules order. Each unit runs only if its inputs are in the
    inventory (including goods made earlier this round) and, for a mine or well, the pool
    has anything left; it then takes its output from the pool, halved (rounded down) while
    the pool is below the scarcity fraction of its start value. Returns (made, used, ran, idle)."""
    made, used, ran, idle = {}, {}, {}, {}
    for t in rules["run_order"]:
        spec = rules["facilities"][t]
        count = firm["facilities"].get(t, 0)
        if count == 0:
            continue
        want = count if run_plan is None else min(count, run_plan.get(t, count))
        if disaster == t:
            want = 0
        n = 0
        pool = spec["pool"]
        for _ in range(want):
            if any(inventory.get(g, 0) < q for g, q in spec["inputs"].items()):
                break
            if pool is not None and pools[pool] <= 0:
                break
            for g, q in spec["inputs"].items():
                inventory[g] -= q
                used[g] = used.get(g, 0) + q
            for g, q in spec["output"].items():
                if pool is not None:
                    if pools[pool] < rules["scarcity_fraction"] * rules["pools"][pool]:
                        q //= 2
                    q = min(q, pools[pool])
                    pools[pool] -= q
                inventory[g] = inventory.get(g, 0) + q
                made[g] = made.get(g, 0) + q
            n += 1
        ran[t] = n
        idle[t] = count - n
    return made, used, ran, idle


def max_drawdown(series):
    """Largest peak-to-trough fall in a series (0 for a series that never falls)."""
    peak = None
    worst = 0
    for v in series:
        if peak is None or v > peak:
            peak = v
        worst = max(worst, peak - v)
    return worst


def resolve_round(match, state, move_texts, players):
    """Resolve one round. `move_texts` maps player name -> text of its move file; `players`
    maps name -> player file. Returns (result, next_state) and never writes anything."""
    rules = match["rules"]
    goods = rules["goods"]
    facs = rules["facilities"]
    rnd = state["round"]
    st = copy_json(state)
    firms = st["firms"]
    seed_hex = round_seed(match["seed"], rnd, move_texts)
    rng = random.Random(int(seed_hex, 16))
    invalid = {}

    def flag(name, where, reason):
        invalid.setdefault(name, []).append({"where": where, "reason": reason})

    # 1. Moves: parse, validate, and let firms with a valid envelope and a player file enter.
    clean = {}
    joined = []
    for name in sorted(move_texts):
        obj, problem = parse_move(move_texts[name])
        if problem is not None:
            flag(name, "file", problem)
            continue
        c, problems, fatal = validate_move(match, st, rnd, name, obj, players)
        for p in problems:
            flag(name, p["where"], p["reason"])
        if fatal:
            continue
        if name not in firms:
            firms[name] = new_firm(rules)
            joined.append(name)
        clean[name] = c
    for name in firms:
        clean.setdefault(name, nothing_move())
    moved = sorted(n for n in move_texts if n in firms)
    absent = sorted(n for n in firms if n not in move_texts)
    cash = {n: cents(f["cash"]) for n, f in firms.items()}
    inv = {n: f["inventory"] for n, f in firms.items()}
    last = {g: (None if st["last_price"][g] is None else cents(st["last_price"][g])) for g in goods}

    # 2. Events, each from its own draw, in a fixed order.
    events = []
    dice = []
    disaster = None
    u = rng.random()
    dice.append(round(u, 9))
    if u < rules["p_disaster"]:
        disaster = rng.choice(sorted(facs))
        events.append({"event": "disaster", "facility": disaster})
    u = rng.random()
    dice.append(round(u, 9))
    if u < rules["p_demand_shock"]:
        good = rng.choice(list(goods))
        lo, hi = rules["shock_range"]
        factor = round(rng.uniform(lo, hi), 9)
        st["shocks"][good] = [factor, rules["shock_rounds"]]
        events.append({"event": "demand_shock", "good": good, "factor": factor, "rounds": rules["shock_rounds"]})
    u = rng.random()
    dice.append(round(u, 9))
    if u < rules["p_windfall"]:
        pool = rng.choice(sorted(st["pools"]))
        st["pools"][pool] += rules["windfall"]
        events.append({"event": "windfall", "pool": pool, "amount": rules["windfall"]})

    # 3. Opex, owed whether or not the firm can pay.
    opex = {}
    for n in sorted(firms):
        due = sum(firms[n]["facilities"].get(t, 0) * cents(facs[t]["opex"]) for t in facs)
        if due:
            cash[n] -= due
            opex[n] = money(due)

    # 4. Builds ordered last round come online.
    for n in sorted(firms):
        f = firms[n]
        for t in facs:
            k = f["pending_builds"].get(t, 0)
            if k:
                f["facilities"][t] = f["facilities"].get(t, 0) + k
                f["pending_builds"][t] = 0

    # 5. Production, firm by firm in name order.
    production = {}
    for n in sorted(firms):
        if not any(firms[n]["facilities"].values()):
            continue
        made, used, ran, idle = run_production(rules, firms[n], inv[n], clean[n]["run"], st["pools"], disaster)
        production[n] = {"made": made, "used": used, "ran": ran, "idle": idle}

    # 6. Forward deliveries due this round.
    deliveries = []
    defaults = []
    remaining = []
    for c in sorted(st["contracts_open"], key=lambda c: c["id"]):
        if c["due"] != rnd:
            remaining.append(c)
            continue
        seller, buyer, good, qty = c["seller"], c["buyer"], c["deliver"], c["qty"]
        value = qty * cents(c["price"])
        seller_ok = inv[seller].get(good, 0) >= qty
        buyer_ok = cash[buyer] >= value
        rec = {"id": c["id"], "seller": seller, "buyer": buyer, "good": good, "qty": qty,
               "price": c["price"], "value": money(value)}
        if seller_ok and buyer_ok:
            inv[seller][good] -= qty
            inv[buyer][good] = inv[buyer].get(good, 0) + qty
            cash[buyer] -= value
            cash[seller] += value
            rec["status"] = "delivered"
        else:
            penalty = half_up(value * rules["default_penalty"])
            rec["status"] = ("both_default" if not seller_ok and not buyer_ok
                             else "seller_default" if not seller_ok else "buyer_default")
            for side, ok, payer, payee in (("seller", seller_ok, seller, buyer), ("buyer", buyer_ok, buyer, seller)):
                if ok:
                    continue
                paid = max(0, min(penalty, cash[payer]))
                cash[payer] -= paid
                cash[payee] += paid
                rep = round(max(0.0, firms[payer]["reputation"] - rules["reputation_drop"]), 9)
                firms[payer]["reputation"] = rep
                defaults.append({"firm": payer, "id": c["id"], "side": side, "penalty": money(penalty),
                                 "paid": money(paid), "reputation": rep})
        deliveries.append(rec)
    st["contracts_open"] = remaining

    # 7. Acceptances of last round's offers become contracts, in offer-id then name order.
    by_offer = {}
    for n in sorted(clean):
        for oid in clean[n]["accept"]:
            by_offer.setdefault(oid, []).append(n)
    open_by_id = {o["id"]: o for o in st["offers_open"]}
    count = {n: 0 for n in firms}
    for c in st["contracts_open"]:
        count[c["seller"]] = count.get(c["seller"], 0) + 1
        count[c["buyer"]] = count.get(c["buyer"], 0) + 1
    accepted = []
    rejected = []
    for oid in sorted(by_offer):
        offer = open_by_id.get(oid)
        taken = False
        for n in by_offer[oid]:
            if offer is None:
                reason = "unknown offer"
            elif taken:
                reason = "taken"
            elif n == offer["seller"]:
                reason = "own offer"
            elif count.get(n, 0) >= rules["max_contracts"]:
                reason = "buyer already has %d open contracts" % rules["max_contracts"]
            elif count.get(offer["seller"], 0) >= rules["max_contracts"]:
                reason = "seller already has %d open contracts" % rules["max_contracts"]
            else:
                contract = {"id": oid, "seller": offer["seller"], "buyer": n, "deliver": offer["deliver"],
                            "qty": offer["qty"], "price": offer["price"], "due": offer["due"], "accepted": rnd}
                st["contracts_open"].append(contract)
                accepted.append(contract)
                count[n] = count.get(n, 0) + 1
                count[offer["seller"]] = count.get(offer["seller"], 0) + 1
                taken = True
                continue
            rejected.append({"firm": n, "id": oid, "reason": reason})
    st["contracts_open"].sort(key=lambda c: c["id"])
    accepted_ids = {c["id"] for c in accepted}
    expired = sorted(o["id"] for o in st["offers_open"] if o["id"] not in accepted_ids)

    # 8. Clearing. Orders are first trimmed to what the firm holds now, after deliveries.
    orders_by_firm = {}
    for n in sorted(firms):
        c = cash[n]
        kept = []
        sold = {g: 0 for g in goods}
        for o in clean[n]["orders"]:
            where = "orders[%d]" % o["seq"]
            if o["side"] == "buy":
                exposure = o["qty"] * o["price"]
                if c < 0 or exposure > c:
                    flag(n, where, "dropped at clearing: cash after deliveries is %.2f" % money(c))
                    continue
                c -= exposure
            else:
                held = inv[n].get(o["good"], 0)
                if sold[o["good"]] + o["qty"] > held:
                    flag(n, where, "dropped at clearing: only %d %s held after deliveries" % (held, o["good"]))
                    continue
                sold[o["good"]] += o["qty"]
            kept.append(o)
        orders_by_firm[n] = kept
    prices = {}
    trades = {}
    for g in goods:
        bids = [o for n in sorted(firms) for o in orders_by_firm[n] if o["side"] == "buy" and o["good"] == g]
        asks = [o for n in sorted(firms) for o in orders_by_firm[n] if o["side"] == "sell" and o["good"] == g]
        ladder, demand, _season = consumer_bids(rules, rnd, st["shocks"], g)
        bids += ladder
        total_bid = sum(o["qty"] for o in bids)
        imp = import_ask(rules, g, total_bid)
        if imp is not None:
            asks.append(imp)
        res = clear(bids, asks)
        rec = {"price": None if res["price"] is None else money(res["price"]), "volume": res["volume"],
               "demand": demand, "bid_qty": total_bid, "ask_qty": sum(o["qty"] for o in asks if o["owner"] != IMPORTS),
               "consumers_bought": 0, "imports_sold": 0}
        if res["price"] is not None:
            p = res["price"]
            last[g] = p
            for o, q in res["fills"]:
                owner = o["owner"]
                if owner == CONSUMERS:
                    rec["consumers_bought"] += q
                    continue
                if owner == IMPORTS:
                    rec["imports_sold"] += q
                    continue
                t = trades.setdefault(owner, {}).setdefault(g, {"bought": 0, "sold": 0, "at": money(p)})
                if o["side"] == "buy":
                    cash[owner] -= q * p
                    inv[owner][g] = inv[owner].get(g, 0) + q
                    t["bought"] += q
                else:
                    cash[owner] += q * p
                    inv[owner][g] -= q
                    t["sold"] += q
        prices[g] = rec

    # 9. New builds are charged; they come online next round.
    builds = {}
    for n in sorted(firms):
        for t in rules["run_order"]:
            k = clean[n]["build"].get(t, 0)
            if not k:
                continue
            cost = cents(facs[t]["cost"])
            can = cash[n] // cost if cash[n] > 0 else 0
            kk = min(k, can)
            if kk < k:
                flag(n, "build.%s" % t, "only %d of %d affordable after clearing" % (kk, k))
            if kk:
                cash[n] -= kk * cost
                firms[n]["pending_builds"][t] = firms[n]["pending_builds"].get(t, 0) + kk
                builds.setdefault(n, {})[t] = kk

    # 10. This round's offers are published; they can be accepted next round only.
    new_offers = []
    for n in sorted(firms):
        for of in clean[n]["offers"]:
            rec = dict(of)
            rec["offered"] = rnd
            new_offers.append(rec)
            firms[n]["offer_seq"] = max(firms[n].get("offer_seq", 0), int(of["id"].rsplit("-", 1)[1]))
    st["offers_open"] = sorted(new_offers, key=lambda o: o["id"])

    # 11. Pools regenerate (capped at their start value); shocks tick down.
    for g in sorted(st["pools"]):
        cap = max(rules["pools"][g], st["pools"][g])
        st["pools"][g] = min(st["pools"][g] + rules["pool_regen"].get(g, 0), cap)
    for g in goods:
        factor, left = st["shocks"][g]
        st["shocks"][g] = [factor, left - 1] if left > 1 else [1.0, 0]

    # 12. Net worth, drawdown, score, standings.
    net_worth, drawdown, scores = {}, {}, {}
    for n in sorted(firms):
        f = firms[n]
        f["cash"] = money(cash[n])
        value = cash[n]
        for g in goods:
            p = last[g] if last[g] is not None else cents(rules["consumer_pmax"][g]) // 2
            value += inv[n].get(g, 0) * p
        for t in facs:
            units = f["facilities"].get(t, 0) + f["pending_builds"].get(t, 0)
            value += units * int(round(facs[t]["cost"] * rules["facility_value"] * 100))
        f["net_worth_history"].append(money(value))
        dd = max_drawdown([cents(v) for v in f["net_worth_history"]])
        net_worth[n] = money(value)
        drawdown[n] = money(dd)
        scores[n] = money(value - half_up(dd * rules["drawdown_weight"]))
    standings = [{"player": n, "score": scores[n], "net_worth": net_worth[n], "drawdown": drawdown[n]}
                 for n in sorted(firms, key=lambda n: (-scores[n], n))]
    st["last_price"] = {g: (None if last[g] is None else money(last[g])) for g in goods}
    st["round"] = rnd + 1
    result = {
        "game": VERSION, "match": match["match"], "round": rnd, "seed": seed_hex, "dice": dice,
        "moved": moved, "absent": absent, "joined": joined,
        "invalid": {n: invalid[n] for n in sorted(invalid)},
        "events": events, "season": round(season_factor(rules, rnd), 9),
        "opex": opex, "production": production, "deliveries": deliveries, "defaults": defaults,
        "contracts": {"accepted": accepted, "rejected": rejected, "expired": expired},
        "prices": prices, "trades": trades, "builds": builds, "offers": st["offers_open"],
        "pools": dict(st["pools"]), "net_worth": net_worth, "drawdown": drawdown, "scores": scores,
        "standings": standings, "final": rnd >= match["rounds"],
    }
    return result, st


def differences(recomputed, committed, path="$"):
    """Paths where two JSON values differ: numbers within 1e-8 are equal, everything else exact."""
    a, b = recomputed, committed
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append("%s.%s only in committed" % (path, k))
            elif k not in b:
                out.append("%s.%s only in recomputed" % (path, k))
            else:
                out += differences(a[k], b[k], "%s.%s" % (path, k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append("%s: %d items recomputed, %d committed" % (path, len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += differences(x, y, "%s[%d]" % (path, i))
    elif is_num(a) and is_num(b) and not isinstance(a, bool) and not isinstance(b, bool):
        if (isinstance(a, float) or isinstance(b, float)) and abs(a - b) > TOLERANCE:
            out.append("%s: %r recomputed, %r committed" % (path, a, b))
        elif isinstance(a, int) and isinstance(b, int) and a != b:
            out.append("%s: %r recomputed, %r committed" % (path, a, b))
    elif type(a) is not type(b) or a != b:
        out.append("%s: %r recomputed, %r committed" % (path, a, b))
    return out


# ----------------------------------------------------------------------------- bots

def price_or(state, rules, good, fraction=0.5):
    """The last clearing price of a good, or `fraction` of the consumers' ceiling before one exists."""
    p = state["last_price"].get(good)
    return p if p is not None else rules["consumer_pmax"][good] * fraction


def scaled_price(state, rules, good, factor, fraction=0.5):
    """`factor` x the last price, or `fraction` x the consumers' ceiling before a price exists."""
    p = state["last_price"].get(good)
    return factor * p if p is not None else rules["consumer_pmax"][good] * fraction


def limit_price(x):
    return max(0.01, round(x, 2))


def merchant_move(rules, match, state, rnd, name, firm):
    """Build a farm, a mine and a well first; sell what next round does not need at 0.8 x the
    last price; buy inputs it is short of at 1.2 x; build a factory when parts pay for it;
    every sixth round, offer parts two rounds ahead at 0.9 x the last price."""
    facs = rules["facilities"]
    goods = rules["goods"]
    owned = {t: firm["facilities"][t] + firm["pending_builds"][t] for t in facs}
    opex = sum(firm["facilities"][t] * facs[t]["opex"] for t in facs)
    avail = firm["cash"] - opex
    build = {}
    if not any(owned.values()):
        for t in ("farm", "mine", "well"):
            if avail >= facs[t]["cost"]:
                build[t] = 1
                avail -= facs[t]["cost"]
    factory = facs["factory"]
    per_part = sum(q * price_or(state, rules, g) for g, q in factory["inputs"].items()
                   if g != "grain") / factory["output"]["parts"]
    if (price_or(state, rules, "parts") > 2 * per_part + 10 and firm["cash"] > 400
            and avail >= factory["cost"] and owned["factory"] < max(1, owned["mine"])):
        build["factory"] = build.get("factory", 0) + 1
        avail -= factory["cost"]
    needs = {g: 0 for g in goods}
    output = {g: 0 for g in goods}
    for t in facs:
        for g, q in facs[t]["inputs"].items():
            needs[g] += owned[t] * q
        for g, q in facs[t]["output"].items():
            output[g] += owned[t] * q
    owed = {g: 0 for g in goods}
    for c in state["contracts_open"]:
        if c["seller"] == name and c["due"] <= rnd + 1:
            owed[c["deliver"]] += c["qty"]
    for o in state["offers_open"]:
        if o["seller"] == name:
            owed[o["deliver"]] += o["qty"]
    inv = firm["inventory"]
    orders = []
    for g in goods:
        surplus = inv[g] - needs[g] - owed[g]
        if surplus > 0:
            # 0.8 x the last price, but never above what a consumer will pay.
            limit = min(scaled_price(state, rules, g, 0.8), rules["consumer_pmax"][g])
            orders.append({"side": "sell", "good": g, "qty": surplus, "limit": limit_price(limit)})
    for g in goods:
        # What it will hold after this round's production and sales, against next round's needs.
        consumed = min(inv[g], needs[g])
        sold = max(0, inv[g] - needs[g] - owed[g])
        short = needs[g] + owed[g] - (inv[g] - consumed - sold + output[g])
        if short > 0:
            limit = limit_price(scaled_price(state, rules, g, 1.2, 0.6))
            qty = min(short, int(avail // limit))
            if qty > 0:
                orders.append({"side": "buy", "good": g, "qty": qty, "limit": limit})
                avail -= qty * limit
    offers = []
    if (rnd % 6 == 0 and firm["facilities"]["factory"] >= 1 and state["last_price"]["parts"] is not None
            and rnd + rules["contract_lead"] <= match["rounds"]):
        offers.append({"id": "%s-%d" % (name, firm["offer_seq"] + 1), "deliver": "parts",
                       "qty": factory["output"]["parts"] * firm["facilities"]["factory"],
                       "price": limit_price(0.9 * state["last_price"]["parts"]), "due": rnd + rules["contract_lead"]})
    body = {}
    if orders:
        body["orders"] = orders
    if build:
        body["build"] = build
    if offers:
        body["offers"] = offers
    return body


HOARDER_DUMP_ROUND = 12


def hoarder_move(rules, match, state, rnd, name, firm):
    """Build mines only, as many as the cash will also run until round 12 (after that, until
    the end of the match); buy the grain they eat; hold every ore until round 12, then dump it
    all at 0.5 x the last price; accept any offer of parts under half the consumers' ceiling,
    whether or not it will be able to pay, and sell whatever it is delivered."""
    facs = rules["facilities"]
    goods = rules["goods"]
    mine = facs["mine"]
    opex = sum(firm["facilities"][t] * facs[t]["opex"] for t in facs)
    avail = firm["cash"] - opex
    grain_price = scaled_price(state, rules, "grain", 1.2, 1.0)
    running = mine["opex"] + mine["inputs"].get("grain", 0) * grain_price
    horizon = max(1, HOARDER_DUMP_ROUND - rnd if rnd < HOARDER_DUMP_ROUND else match["rounds"] - rnd + 1)
    mines = firm["facilities"]["mine"] + firm["pending_builds"]["mine"]
    reserve = 50 + mines * horizon * running
    n = int((avail - reserve) // (mine["cost"] + horizon * running)) if avail > reserve else 0
    build = {"mine": n} if n > 0 else {}
    avail -= n * mine["cost"]
    mines += n
    inv = firm["inventory"]
    orders = []
    per_mine = mine["inputs"].get("grain", 0)
    eaten = min(inv["grain"], firm["facilities"]["mine"] * per_mine)
    short = mines * per_mine - (inv["grain"] - eaten)
    if short > 0:
        # Bid the import price so the mines never starve; what it pays is the clearing price.
        limit = limit_price(market_import_price(rules, "grain"))
        qty = min(short, int(avail // limit))
        if qty > 0:
            orders.append({"side": "buy", "good": "grain", "qty": qty, "limit": limit})
            avail -= qty * limit
    if rnd >= HOARDER_DUMP_ROUND and inv["ore"] > 0:
        orders.append({"side": "sell", "good": "ore", "qty": inv["ore"],
                       "limit": limit_price(min(scaled_price(state, rules, "ore", 0.5, 0.25), rules["consumer_pmax"]["ore"]))})
    for g in goods:
        if g not in ("ore", "grain") and inv[g] > 0:
            orders.append({"side": "sell", "good": g, "qty": inv[g],
                           "limit": limit_price(min(scaled_price(state, rules, g, 0.7, 0.35), rules["consumer_pmax"][g]))})
    room = rules["max_contracts"] - sum(1 for c in state["contracts_open"] if name in (c["seller"], c["buyer"]))
    accept = []
    for o in sorted(state["offers_open"], key=lambda o: o["id"]):
        if (room > 0 and o["deliver"] == "parts" and o["seller"] != name
                and o["price"] < rules["consumer_pmax"]["parts"] / 2):
            accept.append(o["id"])
            room -= 1
    body = {}
    if orders:
        body["orders"] = orders
    if build:
        body["build"] = build
    if accept:
        body["accept"] = accept
    return body


STYLES = {"merchant": merchant_move, "hoarder": hoarder_move}


def bot_move(match, state, rnd, name, style="merchant"):
    """A complete move file (envelope included) for `name` from the committed state."""
    rules = match["rules"]
    firm = state["firms"].get(name) or new_firm(rules)
    move = {"game": VERSION, "match": match["match"], "round": rnd, "player": name}
    move.update(STYLES[style](rules, match, state, rnd, name, firm))
    return move


# ----------------------------------------------------------------------------- render

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK = "#172033"
MUTED = "#6b7280"
GRID = "#e5e7eb"


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def nice_range(lo, hi, n=4):
    """A rounded (low, high, step) that covers [lo, hi] in about n steps."""
    lo = min(lo, 0)
    hi = max(hi, lo + 1)
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = mag
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if raw <= step:
            break
    low = math.floor(lo / step) * step
    high = math.ceil(hi / step) * step
    if high <= low:
        high = low + step
    return low, high, step


def fmt_tick(v):
    if abs(v - round(v)) < 1e-9:
        return "%d" % round(v)
    return ("%.2f" % v).rstrip("0").rstrip(".")


def line_chart(x0, y0, w, h, title, series, rounds, y_label, rules_lines=()):
    """One chart as SVG text. `series` is a list of (label, colour, values) with None for gaps;
    `rules_lines` is a list of (label, value) drawn as dashed horizontal lines."""
    labelled = [label for label, _, _ in series if label] if len(series) <= 6 else []
    left, top, bottom = 52, 26, 28
    right = 16 + (7 * max(len(label) for label in labelled) + 6 if labelled else 0)
    px0, py0 = x0 + left, y0 + top
    pw, ph = w - left - right, h - top - bottom
    values = [v for _, _, vs in series for v in vs if v is not None] + [v for _, v in rules_lines]
    lo, hi, step = nice_range(min(values) if values else 0, max(values) if values else 1)
    n = max(1, len(rounds))

    def sx(i):
        return px0 + (pw * (i + 0.5) / n if n == 1 else pw * i / (n - 1))

    def sy(v):
        return py0 + ph - ph * (v - lo) / (hi - lo)

    out = ['<text x="%g" y="%g" font-size="13" font-weight="600" fill="%s">%s</text>' % (x0 + left, y0 + 15, INK, esc(title))]
    v = lo
    while v <= hi + step * 1e-9:
        y = sy(v)
        out.append('<line x1="%g" y1="%.1f" x2="%g" y2="%.1f" stroke="%s" stroke-width="1"/>' % (px0, y, px0 + pw, y, GRID))
        out.append('<text x="%g" y="%.1f" font-size="10" fill="%s" text-anchor="end">%s</text>' % (px0 - 6, y + 3.5, MUTED, fmt_tick(v)))
        v += step
    out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1"/>' % (px0, py0 + ph, px0 + pw, py0 + ph, MUTED))
    every = 1 if n <= 12 else 2 if n <= 30 else 5
    for i, r in enumerate(rounds):
        if (r % every == 0 and every > 1) or every == 1 or i == 0:
            out.append('<text x="%.1f" y="%g" font-size="10" fill="%s" text-anchor="middle">%d</text>' % (sx(i), py0 + ph + 14, MUTED, r))
    out.append('<text x="%g" y="%g" font-size="10" fill="%s" text-anchor="end">round</text>' % (px0 + pw, py0 + ph + 26, MUTED))
    out.append('<text x="%g" y="%g" font-size="10" fill="%s" text-anchor="end">%s</text>' % (px0 - 6, y0 + 15, MUTED, esc(y_label)))
    for label, value in rules_lines:
        y = sy(value)
        out.append('<line x1="%g" y1="%.1f" x2="%g" y2="%.1f" stroke="%s" stroke-width="1" stroke-dasharray="4 3"/>' % (px0, y, px0 + pw, y, MUTED))
        out.append('<text x="%g" y="%.1f" font-size="9" fill="%s" text-anchor="end">%s</text>' % (px0 + pw, y - 3, MUTED, esc(label)))
    for label, colour, vs in series:
        segment = []
        for i, v in enumerate(vs):
            if v is None:
                if len(segment) > 1:
                    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (" ".join(segment), colour))
                segment = []
            else:
                segment.append("%.1f,%.1f" % (sx(i), sy(v)))
        if len(segment) > 1:
            out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (" ".join(segment), colour))
        for i, v in enumerate(vs):
            if v is not None:
                out.append('<circle cx="%.1f" cy="%.1f" r="2.2" fill="%s"/>' % (sx(i), sy(v), colour))
    # Direct labels at each line's last point, pushed apart when they would overlap.
    ends = []
    for label, colour, vs in series:
        last_i = max((i for i, v in enumerate(vs) if v is not None), default=None)
        if label in labelled and last_i is not None:
            ends.append([sy(vs[last_i]) + 3.5, sx(last_i) + 5, label])
    ends.sort()
    for k in range(1, len(ends)):
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 11)
    for y, x, label in ends:
        out.append('<text x="%.1f" y="%.1f" font-size="10" fill="%s">%s</text>' % (x, y, INK, esc(label)))
    return "\n".join(out)


def render_svg(match, results):
    """Four price charts and one net-worth chart for the resolved rounds given, as an SVG string."""
    rules = match["rules"]
    goods = rules["goods"]
    rounds = [r["round"] for r in results]
    width, height = 960, 760
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="title desc" font-family="system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif">' % (width, height, width, height),
           '<title id="title">Market %s, rounds %d to %d</title>' % (esc(match["match"]), rounds[0], rounds[-1]),
           '<desc id="desc">Clearing price of each good per round, and the net worth of each firm.</desc>',
           '<rect width="100%%" height="100%%" fill="#fcfcfb"/>',
           '<text x="24" y="30" font-size="18" font-weight="600" fill="%s">Market · %s</text>' % (INK, esc(match["match"])),
           '<text x="24" y="48" font-size="11" fill="%s">seed %s · %d of %d rounds · clearing price per good, then net worth per firm</text>' % (MUTED, esc(match["seed"]), len(results), match["rounds"])]
    cw, ch = 456, 196
    for k, g in enumerate(goods):
        x0 = 16 + (k % 2) * (cw + 16)
        y0 = 62 + (k // 2) * (ch + 10)
        values = [r["prices"].get(g, {}).get("price") for r in results]
        lines = [("Pmax %s" % fmt_tick(rules["consumer_pmax"][g]), rules["consumer_pmax"][g])]
        if g in rules["import_goods"]:
            lines.append(("imports %s" % fmt_tick(rules["consumer_pmax"][g] * rules["import_markup"]), rules["consumer_pmax"][g] * rules["import_markup"]))
        out.append(line_chart(x0, y0, cw, ch, "%s price" % g, [("", PALETTE[0], values)], rounds, "price", lines))
    firms = sorted({n for r in results for n in r["net_worth"]})
    series = []
    for i, n in enumerate(firms):
        colour = PALETTE[i] if i < len(PALETTE) else MUTED
        series.append((n, colour, [r["net_worth"].get(n) for r in results]))
    y0 = 62 + 2 * (ch + 10)
    out.append(line_chart(16, y0, width - 32, height - y0 - 36, "net worth per firm", series, rounds, "net worth"))
    lx = 24
    ly = height - 14
    for n, colour, _ in series:
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"/>' % (lx, ly - 4, lx + 18, ly - 4, colour))
        out.append('<text x="%d" y="%d" font-size="11" fill="%s">%s</text>' % (lx + 24, ly, INK, esc(n)))
        lx += 24 + 7 * len(n) + 24
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------- files

def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(obj), encoding="utf-8")


def parse_round(text):
    try:
        rnd = int(text)
    except ValueError:
        fail("round must be a number like 7 or 007, not %r" % text)
    if rnd < 1:
        fail("rounds start at 1")
    return rnd


def round_dir(match_dir, rnd):
    return Path(match_dir) / "rounds" / ("%03d" % rnd)


def load_match(match_dir):
    path = Path(match_dir) / "match.json"
    if not path.exists():
        fail("%s not found; is %s a match directory?" % (path, match_dir))
    match = read_json(path)
    if match.get("game") != VERSION:
        fail("%s is a %r match, not %r" % (path, match.get("game"), VERSION))
    return match


def load_state(match_dir, rnd):
    path = round_dir(match_dir, rnd) / "state.json"
    if not path.exists():
        fail("%s not found; resolve round %d first" % (path, rnd - 1) if rnd > 1 else "%s not found" % path)
    state = read_json(path)
    if state.get("round") != rnd:
        fail("%s says round %r, not %d" % (path, state.get("round"), rnd))
    return state


def load_players(match_dir):
    players = {}
    pdir = Path(match_dir) / "players"
    if not pdir.is_dir():
        return players
    for path in sorted(pdir.glob("*.json")):
        name = path.stem
        if not NAME_RE.match(name):
            continue
        try:
            p = read_json(path)
        except Exception:
            continue
        if isinstance(p, dict) and p.get("name") == name and is_int(p.get("joined")):
            players[name] = p
    return players


def load_moves(match_dir, rnd):
    """Text of every move file present for the round, keyed by file stem."""
    mdir = round_dir(match_dir, rnd) / "moves"
    moves = {}
    if mdir.is_dir():
        for path in sorted(mdir.glob("*.json")):
            moves[path.stem] = path.read_text(encoding="utf-8", errors="replace")
    return moves


def current_round(match_dir):
    """The highest round with a state.json and no result.json, or None."""
    rdir = Path(match_dir) / "rounds"
    if not rdir.is_dir():
        return None
    best = None
    for d in sorted(rdir.iterdir()):
        if d.is_dir() and d.name.isdigit() and (d / "state.json").exists() and not (d / "result.json").exists():
            best = int(d.name)
    return best


def last_resolved_round(match_dir):
    rdir = Path(match_dir) / "rounds"
    best = None
    if rdir.is_dir():
        for d in sorted(rdir.iterdir()):
            if d.is_dir() and d.name.isdigit() and (d / "result.json").exists():
                best = int(d.name)
    return best


def check_round(match_dir, match, rnd):
    """Recompute a resolved round and compare with the committed files. Returns difference list."""
    state = load_state(match_dir, rnd)
    result_path = round_dir(match_dir, rnd) / "result.json"
    next_path = round_dir(match_dir, rnd + 1) / "state.json"
    if not result_path.exists():
        fail("%s does not exist; nothing to check" % result_path)
    result, nxt = resolve_round(match, state, load_moves(match_dir, rnd), load_players(match_dir))
    diffs = ["result" + d[1:] for d in differences(result, read_json(result_path))]
    if next_path.exists():
        diffs += ["next state" + d[1:] for d in differences(nxt, read_json(next_path))]
    else:
        diffs.append("%s is missing" % next_path)
    return diffs


# ----------------------------------------------------------------------------- commands

def cmd_new(args):
    match_dir = Path(args.match)
    if (match_dir / "match.json").exists():
        fail("%s already has a match.json; new never overwrites" % match_dir)
    if not 1 <= args.rounds <= 200:
        fail("--rounds must be from 1 to 200")
    match = {"game": VERSION, "match": match_dir.name, "seed": args.seed, "rounds": args.rounds,
             "seats": None, "rules": default_rules()}
    write_json(match_dir / "match.json", match)
    write_json(round_dir(match_dir, 1) / "state.json", initial_state(match))
    print("new match %s: %d rounds, seed %r; round 1 is open" % (match_dir, args.rounds, args.seed))


def cmd_join(args):
    name = args.player
    if not NAME_RE.match(name):
        fail("player names are 2 to 32 lowercase letters, digits and hyphens")
    match = load_match(args.match)
    path = Path(args.match) / "players" / ("%s.json" % name)
    if path.exists():
        fail("%s exists; player files are never overwritten" % path)
    rnd = current_round(args.match)
    if rnd is None or rnd > match["rounds"]:
        fail("this match has no open round to join")
    if args.seat is not None:
        print("Market has no seats; --seat ignored", file=sys.stderr)
    write_json(path, {"name": name, "game": VERSION, "match": match["match"], "joined": rnd,
                      "session": args.session, "seat": None})
    print("%s joins %s in round %d; the firm exists from the first round it moves in" % (name, match["match"], rnd))


def cmd_bot(args):
    name = args.player
    if not NAME_RE.match(name):
        fail("player names are 2 to 32 lowercase letters, digits and hyphens")
    match = load_match(args.match)
    rnd = parse_round(args.round)
    if rnd > match["rounds"]:
        fail("this match has %d rounds" % match["rounds"])
    state = load_state(args.match, rnd)
    if (round_dir(args.match, rnd) / "result.json").exists():
        fail("round %d is already resolved" % rnd)
    players = load_players(args.match)
    if name not in state["firms"] and not eligible(players, name, rnd):
        fail("%s has no player file for round %d; join first" % (name, rnd))
    path = round_dir(args.match, rnd) / "moves" / ("%s.json" % name)
    if path.exists() and not args.force:
        fail("%s exists; pass --force to replace it" % path)
    move = bot_move(match, state, rnd, name, args.style)
    _clean, problems, fatal = validate_move(match, state, rnd, name, move, players)
    if problems or fatal:
        print("bot produced problems, writing the do-nothing move instead: %s" % problems, file=sys.stderr)
        move = {"game": VERSION, "match": match["match"], "round": rnd, "player": name}
    write_json(path, move)
    print("wrote %s (%s)" % (path, args.style))


def describe(problems):
    return "\n".join("  %s: %s" % (p["where"], p["reason"]) for p in problems)


def cmd_validate(args):
    match = load_match(args.match)
    rnd = parse_round(args.round)
    state = load_state(args.match, rnd)
    path = Path(args.move)
    if not path.exists():
        fail("%s not found" % path)
    name = path.stem
    obj, problem = parse_move(path.read_text(encoding="utf-8", errors="replace"))
    if problem is not None:
        print("%s: rejected\n  file: %s" % (path, problem))
        sys.exit(1)
    _clean, problems, fatal = validate_move(match, state, rnd, name, obj, load_players(args.match))
    if fatal:
        print("%s: rejected\n%s" % (path, describe(problems)))
        sys.exit(1)
    if problems:
        print("%s: accepted with %d part(s) dropped\n%s" % (path, len(problems), describe(problems)))
        sys.exit(1)
    print("%s: ok" % path)


def summarise(result):
    prices = ", ".join("%s %s" % (g, "-" if p["price"] is None else "%.2f" % p["price"]) for g, p in sorted(result["prices"].items()))
    events = "; ".join("%s(%s)" % (e["event"], ", ".join("%s %s" % (k, v) for k, v in sorted(e.items()) if k != "event"))
                       for e in result["events"]) or "no events"
    line = "round %d: %s; %s" % (result["round"], events, prices)
    if result["defaults"]:
        line += "; defaults: " + ", ".join("%s on %s" % (d["firm"], d["id"]) for d in result["defaults"])
    if result["absent"]:
        line += "; absent: " + ", ".join(result["absent"])
    if result["invalid"]:
        line += "; invalid: " + ", ".join(sorted(result["invalid"]))
    return line


def cmd_resolve(args):
    match = load_match(args.match)
    rnd = parse_round(args.round)
    if rnd > match["rounds"]:
        fail("this match has %d rounds" % match["rounds"])
    if args.check:
        diffs = check_round(args.match, match, rnd)
        if diffs:
            print("round %d: %d difference(s)" % (rnd, len(diffs)))
            for d in diffs:
                print("  " + d)
            sys.exit(1)
        print("round %d: recomputed result and next state match the committed files" % rnd)
        return
    result_path = round_dir(args.match, rnd) / "result.json"
    if result_path.exists():
        fail("%s exists; resolve never overwrites a result (use --check to recompute and compare)" % result_path)
    state = load_state(args.match, rnd)
    players = load_players(args.match)
    moves = load_moves(args.match, rnd)
    expected = set(state["firms"]) | {n for n in players if eligible(players, n, rnd)}
    missing = sorted(n for n in expected if n not in moves)
    if missing and not args.allow_absent:
        fail("no move for %s; pass --allow-absent to give them the do-nothing move" % ", ".join(missing))
    result, nxt = resolve_round(match, state, moves, players)
    write_json(result_path, result)
    write_json(round_dir(args.match, rnd + 1) / "state.json", nxt)
    print(summarise(result))
    if result["final"]:
        print("final standings: " + ", ".join("%d. %s %.2f" % (i + 1, s["player"], s["score"]) for i, s in enumerate(result["standings"])))


def cmd_verify(args):
    match = load_match(args.match)
    bad = 0
    first = round_dir(args.match, 1) / "state.json"
    if not first.exists():
        fail("%s is missing" % first)
    diffs = differences(initial_state(match), read_json(first))
    if diffs:
        bad += 1
        print("rounds/001/state.json differs from what new writes for this match.json:")
        for d in diffs:
            print("  " + d)
    rnd = 1
    checked = 0
    while (round_dir(args.match, rnd) / "result.json").exists() and rnd <= match["rounds"]:
        diffs = check_round(args.match, match, rnd)
        checked += 1
        if diffs:
            bad += 1
            print("round %03d: %d difference(s)" % (rnd, len(diffs)))
            for d in diffs[:20]:
                print("  " + d)
        else:
            print("round %03d: ok" % rnd)
        rnd += 1
    if checked == 0:
        print("no resolved rounds yet; round 1 state ok" if not bad else "no resolved rounds")
    if bad:
        print("verify FAILED: %d problem(s)" % bad)
        sys.exit(1)
    print("verify ok: %d round(s) recomputed and identical%s" % (checked, ", match complete" if checked == match["rounds"] else ""))


def cmd_score(args):
    match = load_match(args.match)
    rnd = last_resolved_round(args.match)
    if rnd is None:
        fail("no round has been resolved yet")
    result = read_json(round_dir(args.match, rnd) / "result.json")
    print("%s after round %d of %d%s" % (match["match"], rnd, match["rounds"], " (final)" if result["final"] else ""))
    print("%-4s %-34s %12s %12s %12s" % ("", "player", "score", "net worth", "drawdown"))
    for i, s in enumerate(result["standings"]):
        print("%-4s %-34s %12.2f %12.2f %12.2f" % ("%d." % (i + 1), s["player"], s["score"], s["net_worth"], s["drawdown"]))


def cmd_render(args):
    match = load_match(args.match)
    last = last_resolved_round(args.match)
    if last is None:
        fail("no round has been resolved yet; nothing to draw")
    upto = parse_round(args.round) if args.round else last
    results = []
    for rnd in range(1, upto + 1):
        path = round_dir(args.match, rnd) / "result.json"
        if not path.exists():
            break
        results.append(read_json(path))
    if not results:
        fail("no results up to round %d" % upto)
    sys.stdout.write(render_svg(match, results))


def cmd_book(args):
    match = load_match(args.match)
    rules = match["rules"]
    rnd = parse_round(args.round)
    state = load_state(args.match, rnd)
    players = load_players(args.match)
    moves = load_moves(args.match, rnd)
    orders = []
    for name in sorted(moves):
        obj, problem = parse_move(moves[name])
        if problem is not None:
            print("%s: %s (ignored)" % (name, problem))
            continue
        clean, problems, fatal = validate_move(match, state, rnd, name, obj, players)
        if fatal:
            print("%s: rejected (%s)" % (name, problems[0]["reason"]))
            continue
        if problems:
            print("%s: %d part(s) would be dropped" % (name, len(problems)))
        orders += clean["orders"]
    print("book for round %d from %d move file(s), assuming no new event this round:" % (rnd, len(moves)))
    for g in rules["goods"]:
        bids = [o for o in orders if o["side"] == "buy" and o["good"] == g]
        asks = [o for o in orders if o["side"] == "sell" and o["good"] == g]
        ladder, demand, _season = consumer_bids(rules, rnd, state["shocks"], g)
        bids += ladder
        imp = import_ask(rules, g, sum(o["qty"] for o in bids))
        if imp is not None:
            asks.append(imp)
        res = clear(bids, asks)
        print("\n%s  (consumers want %d; last price %s)" % (g, demand, "none" if state["last_price"][g] is None else "%.2f" % state["last_price"][g]))
        agg_b, agg_a = {}, {}
        for o in bids:
            agg_b[o["price"]] = agg_b.get(o["price"], 0) + o["qty"]
        for o in asks:
            if o["owner"] != IMPORTS:
                agg_a[o["price"]] = agg_a.get(o["price"], 0) + o["qty"]
        print("  bids: " + (", ".join("%d @ %.2f" % (q, p / 100) for p, q in sorted(agg_b.items(), reverse=True)) or "none"))
        asks_text = ", ".join("%d @ %.2f" % (q, p / 100) for p, q in sorted(agg_a.items()))
        if imp is not None:
            asks_text += (", " if asks_text else "") + "imports @ %.2f" % (imp["price"] / 100)
        print("  asks: " + (asks_text or "none"))
        if res["price"] is None:
            print("  would clear: no trade")
        else:
            print("  would clear: %d at %.2f" % (res["volume"], res["price"] / 100))


def cmd_demo(args):
    started = time.time()
    names = [n.strip() for n in args.players.split(",") if n.strip()]
    for n in names:
        if not NAME_RE.match(n):
            fail("bad player name %r" % n)
    cmd_new(argparse.Namespace(match=args.match, seed=args.seed, rounds=args.rounds))
    match = load_match(args.match)
    for n in names:
        cmd_join(argparse.Namespace(match=args.match, player=n, seat=None, session=None))
    players = load_players(args.match)
    disasters, defaults, shocks, windfalls = [], [], [], []
    for rnd in range(1, args.rounds + 1):
        state = load_state(args.match, rnd)
        for n in names:
            style = "hoarder" if n.startswith("hoarder") else "merchant"
            move = bot_move(match, state, rnd, n, style)
            _c, problems, fatal = validate_move(match, state, rnd, n, move, players)
            if problems or fatal:
                fail("bot %s wrote an invalid move in round %d: %s" % (n, rnd, problems))
            write_json(round_dir(args.match, rnd) / "moves" / ("%s.json" % n), move)
        result, nxt = resolve_round(match, state, load_moves(args.match, rnd), players)
        write_json(round_dir(args.match, rnd) / "result.json", result)
        write_json(round_dir(args.match, rnd + 1) / "state.json", nxt)
        print(summarise(result))
        for e in result["events"]:
            (disasters if e["event"] == "disaster" else shocks if e["event"] == "demand_shock" else windfalls).append((rnd, e))
        defaults += [(rnd, d) for d in result["defaults"]]
    elapsed = time.time() - started
    print("\nfinal standings after %d rounds:" % args.rounds)
    for i, s in enumerate(result["standings"]):
        print("  %d. %-12s score %9.2f  net worth %9.2f  drawdown %8.2f  reputation %.1f"
              % (i + 1, s["player"], s["score"], s["net_worth"], s["drawdown"], nxt["firms"][s["player"]]["reputation"]))
    print("disasters: " + (", ".join("round %d %s" % (r, e["facility"]) for r, e in disasters) or "none"))
    print("demand shocks: " + (", ".join("round %d %s x%.3f" % (r, e["good"], e["factor"]) for r, e in shocks) or "none"))
    print("windfalls: " + (", ".join("round %d %s +%d" % (r, e["pool"], e["amount"]) for r, e in windfalls) or "none"))
    print("defaults: " + (", ".join("round %d %s (%s on %s)" % (r, d["firm"], d["side"], d["id"]) for r, d in defaults) or "none"))
    print("pools at the end: %s" % ", ".join("%s %d" % kv for kv in sorted(nxt["pools"].items())))
    print("wall time: %.2f s" % elapsed)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="market.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="command", required=True)

    p = sub.add_parser("new", help="create a match directory with match.json and the round-1 state")
    p.add_argument("match", help="match directory, e.g. games/market/001-opening-bell")
    p.add_argument("--seed", required=True, help="text that seeds every round together with the moves")
    p.add_argument("--rounds", type=int, default=24, help="number of rounds (default 24)")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("join", help="write players/<name>.json for the open round (Market has no seats)")
    p.add_argument("match")
    p.add_argument("--player", required=True, help="2 to 32 lowercase letters, digits and hyphens")
    p.add_argument("--seat", type=int, help="accepted for the common command set; ignored")
    p.add_argument("--session", help="a session link or name, recorded in the player file")
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("bot", help="write a legal move for a player from the committed state")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--player", required=True)
    p.add_argument("--style", choices=sorted(STYLES), default="merchant", help="merchant (default) or hoarder")
    p.add_argument("--force", action="store_true", help="replace an existing move file")
    p.set_defaults(func=cmd_bot)

    p = sub.add_parser("validate", help="check a move file against the round's state; exit 1 if any part would be rejected")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("move", help="path to the move file; its file name is the player name")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("book", help="print the bid and ask ladders per good from the moves present, and what would clear")
    p.add_argument("match")
    p.add_argument("round")
    p.set_defaults(func=cmd_book)

    p = sub.add_parser("resolve", help="resolve a round: write result.json and the next state.json")
    p.add_argument("match")
    p.add_argument("round")
    p.add_argument("--allow-absent", action="store_true", help="give players without a move the do-nothing move")
    p.add_argument("--check", action="store_true", help="recompute in memory and compare with the committed files")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("verify", help="recompute every resolved round and compare with the committed files")
    p.add_argument("match")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("score", help="print the standings after the last resolved round")
    p.add_argument("match")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("render", help="write an SVG of prices per good and net worth per firm to stdout")
    p.add_argument("match")
    p.add_argument("round", nargs="?", help="draw up to this round (default: the last resolved)")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("demo", help="new match, four bots, every round resolved: a complete example")
    p.add_argument("match", help="a directory that does not yet hold a match")
    p.add_argument("--seed", required=True)
    p.add_argument("--rounds", type=int, default=24)
    p.add_argument("--players", default="merchant-1,merchant-2,hoarder-3,merchant-4",
                   help="comma-separated names; a name starting with 'hoarder' plays that style")
    p.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
