"""Tests for made/market.py, the Market referee. Pure-engine tests drive the functions with
dicts; the command tests build a small match in a temporary directory through main()."""
import contextlib
import io
import json
import random
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "made"))
import market  # noqa: E402

GOODS = ("ore", "grain", "fuel", "parts")


def order(owner, side, good, qty, price, seq=0):
    return {"owner": owner, "side": side, "good": good, "qty": qty, "price": market.cents(price), "seq": seq}


def fills_by_owner(result):
    out = {}
    for o, q in result["fills"]:
        out[o["owner"]] = out.get(o["owner"], 0) + q
    return out


def make_match(seed="test", rounds=6, match_id="t-match"):
    return {"game": market.VERSION, "match": match_id, "seed": seed, "rounds": rounds,
            "seats": None, "rules": market.default_rules()}


def make_firm(rules, **over):
    firm = market.new_firm(rules)
    for key, value in over.items():
        if isinstance(value, dict):
            firm[key].update(value)
        else:
            firm[key] = value
    return firm


def envelope(match, rnd, name, **body):
    move = {"game": market.VERSION, "match": match["match"], "round": rnd, "player": name}
    move.update(body)
    return move


def text(obj):
    return json.dumps(obj)


class ClearingTests(unittest.TestCase):
    def test_no_trade_when_best_bid_below_best_ask(self):
        res = market.clear([order("a", "buy", "ore", 5, 3.0)], [order("b", "sell", "ore", 5, 5.0)])
        self.assertIsNone(res["price"])
        self.assertEqual(res["volume"], 0)
        self.assertEqual(res["fills"], [])

    def test_full_fill_at_midpoint(self):
        res = market.clear([order("a", "buy", "ore", 10, 5.0)], [order("b", "sell", "ore", 10, 3.0)])
        self.assertEqual(res["price"], 400)
        self.assertEqual(res["volume"], 10)
        self.assertEqual(fills_by_owner(res), {"a": 10, "b": 10})

    def test_half_cent_midpoint_rounds_up(self):
        res = market.clear([order("a", "buy", "ore", 1, 4.01)], [order("b", "sell", "ore", 1, 4.00)])
        self.assertEqual(res["price"], 401)

    def test_largest_quantity_and_marginal_orders(self):
        bids = [order("a", "buy", "ore", 100, 10.0)]
        asks = [order("b", "sell", "ore", 50, 4.0), order("c", "sell", "ore", 100, 20.0)]
        res = market.clear(bids, asks)
        self.assertEqual(res["volume"], 50)
        self.assertEqual(res["price"], 700)
        self.assertEqual(fills_by_owner(res), {"a": 50, "b": 50})

    def test_pro_rata_at_the_margin_with_remainder_in_name_order(self):
        asks = [order("beta", "sell", "ore", 10, 3.0), order("alpha", "sell", "ore", 10, 3.0)]
        res = market.clear([order("c", "buy", "ore", 15, 5.0)], asks)
        self.assertEqual(res["volume"], 15)
        self.assertEqual(fills_by_owner(res), {"c": 15, "alpha": 8, "beta": 7})
        total_asks = sum(q for o, q in res["fills"] if o["side"] == "sell")
        self.assertEqual(total_asks, 15)

    def test_background_agents_lose_ties(self):
        rules = market.default_rules()
        ladder, qty, _ = market.consumer_bids(rules, 4, {}, "ore")
        bids = ladder + [order("zed", "buy", "ore", 1, 8.0)]
        res = market.clear(bids, [order("s", "sell", "ore", 2, 1.0)])
        by = fills_by_owner(res)
        self.assertEqual(res["volume"], 2)
        self.assertEqual(by["zed"], 1)
        self.assertEqual(by[market.CONSUMERS], 1)

    def test_consumer_ladder_shape(self):
        rules = market.default_rules()
        ladder, qty, season = market.consumer_bids(rules, 4, {}, "grain")
        self.assertEqual(qty, 40)
        self.assertAlmostEqual(season, 1.0, places=9)
        self.assertEqual([o["price"] for o in ladder], [500, 450, 400, 350, 300, 250, 200, 150, 100, 50])
        self.assertEqual([o["qty"] for o in ladder], [4] * 10)
        ladder, qty, _ = market.consumer_bids(rules, 4, {"grain": [1.075, 2]}, "grain")
        self.assertEqual(qty, 43)
        self.assertEqual([o["qty"] for o in ladder], [7] + [4] * 9)
        ladder, qty, _ = market.consumer_bids(rules, 2, {}, "ore")
        self.assertEqual(qty, 25)
        self.assertEqual(ladder[0]["qty"], 7)

    def test_imports_bound_the_price(self):
        rules = market.default_rules()
        imp = market.import_ask(rules, "ore", 100)
        self.assertEqual(imp["price"], 1200)
        res = market.clear([order("a", "buy", "ore", 100, 20.0)], [imp])
        self.assertEqual((res["price"], res["volume"]), (1600, 100))
        res = market.clear([order("a", "buy", "ore", 100, 12.0)], [market.import_ask(rules, "ore", 100)])
        self.assertEqual((res["price"], res["volume"]), (1200, 100))
        ladder, qty, _ = market.consumer_bids(rules, 4, {}, "ore")
        res = market.clear(ladder, [market.import_ask(rules, "ore", qty)])
        self.assertIsNone(res["price"])
        self.assertIsNone(market.import_ask(rules, "parts", 10))


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.rules = market.default_rules()
        self.pools = dict(self.rules["pools"])

    def run_firm(self, facilities, inventory, run=None, disaster=None, pools=None):
        firm = make_firm(self.rules, facilities=facilities)
        inv = {g: 0 for g in GOODS}
        inv.update(inventory)
        pools = self.pools if pools is None else pools
        made, used, ran, idle = market.run_production(self.rules, firm, inv, run, pools, disaster)
        return made, used, ran, idle, inv, pools

    def test_mine_without_grain_idles(self):
        made, used, ran, idle, inv, pools = self.run_firm({"mine": 1}, {})
        self.assertEqual((ran["mine"], idle["mine"]), (0, 1))
        self.assertEqual(made, {})
        self.assertEqual(pools["ore"], 3000)

    def test_factory_short_of_fuel_idles(self):
        made, used, ran, idle, inv, _ = self.run_firm({"factory": 1}, {"ore": 8, "grain": 1, "fuel": 3})
        self.assertEqual((ran["factory"], idle["factory"]), (0, 1))
        self.assertEqual(inv["ore"], 8)
        made, used, ran, idle, inv, _ = self.run_firm({"factory": 1}, {"ore": 8, "grain": 1, "fuel": 4})
        self.assertEqual(ran["factory"], 1)
        self.assertEqual(inv, {"ore": 0, "grain": 0, "fuel": 0, "parts": 4})

    def test_farm_feeds_mine_in_the_same_round(self):
        made, used, ran, idle, inv, pools = self.run_firm({"farm": 1, "mine": 1}, {})
        self.assertEqual(made, {"grain": 8, "ore": 6})
        self.assertEqual(inv["grain"], 7)
        self.assertEqual(inv["ore"], 6)
        self.assertEqual(pools["ore"], 2994)

    def test_run_plan_and_disaster(self):
        made, used, ran, idle, inv, _ = self.run_firm({"mine": 2}, {"grain": 5}, run={"mine": 1})
        self.assertEqual((ran["mine"], idle["mine"]), (1, 1))
        made, used, ran, idle, inv, _ = self.run_firm({"mine": 2, "farm": 1}, {"grain": 5}, disaster="mine")
        self.assertEqual((ran["mine"], idle["mine"], ran["farm"]), (0, 2, 1))

    def test_pool_depletion_and_scarcity_halving(self):
        pools = {"ore": 700, "fuel": 2000}
        made, used, ran, idle, inv, pools = self.run_firm({"mine": 1}, {"grain": 1}, pools=pools)
        self.assertEqual(made["ore"], 3)
        self.assertEqual(pools["ore"], 697)
        pools = {"ore": 5, "fuel": 2000}
        made, used, ran, idle, inv, pools = self.run_firm({"mine": 3}, {"grain": 3}, pools=pools)
        self.assertEqual(made["ore"], 5)
        self.assertEqual(pools["ore"], 0)
        self.assertEqual((ran["mine"], idle["mine"]), (2, 1))
        self.assertEqual(inv["grain"], 1)
        pools = {"ore": 3000, "fuel": 400}
        made, used, ran, idle, inv, pools = self.run_firm({"well": 1}, {"grain": 1}, pools=pools)
        self.assertEqual(made["fuel"], 2)


class EngineRoundTests(unittest.TestCase):
    """resolve_round on hand-built states."""

    def setUp(self):
        self.match = make_match()
        self.rules = self.match["rules"]
        self.players = {"ann": {"joined": 1}, "bob": {"joined": 1}, "cat": {"joined": 1}}

    def state_with(self, rnd, firms, **over):
        state = market.initial_state(self.match)
        state["round"] = rnd
        state["firms"] = firms
        state.update(over)
        return state

    def resolve(self, state, moves):
        texts = {n: text(envelope(self.match, state["round"], n, **body)) for n, body in moves.items()}
        return market.resolve_round(self.match, state, texts, self.players)

    def contract(self, due, qty=4, price=30.0):
        return {"id": "ann-1", "seller": "ann", "buyer": "bob", "deliver": "parts", "qty": qty,
                "price": price, "due": due, "accepted": 1}

    def test_contract_delivery_moves_goods_and_cash(self):
        firms = {"ann": make_firm(self.rules, inventory={"parts": 4}), "bob": make_firm(self.rules)}
        state = self.state_with(3, firms, contracts_open=[self.contract(3)])
        result, nxt = self.resolve(state, {"ann": {}, "bob": {}})
        self.assertEqual(result["deliveries"][0]["status"], "delivered")
        self.assertEqual(nxt["firms"]["ann"]["inventory"]["parts"], 0)
        self.assertEqual(nxt["firms"]["bob"]["inventory"]["parts"], 4)
        self.assertEqual(nxt["firms"]["ann"]["cash"], 1120.0)
        self.assertEqual(nxt["firms"]["bob"]["cash"], 880.0)
        self.assertEqual(nxt["contracts_open"], [])
        self.assertEqual(result["defaults"], [])

    def test_buyer_default_pays_what_it_has_and_loses_reputation(self):
        firms = {"ann": make_firm(self.rules, inventory={"parts": 4}), "bob": make_firm(self.rules, cash=10.0)}
        state = self.state_with(3, firms, contracts_open=[self.contract(3)])
        result, nxt = self.resolve(state, {"ann": {}, "bob": {}})
        self.assertEqual(result["deliveries"][0]["status"], "buyer_default")
        d = result["defaults"][0]
        self.assertEqual((d["firm"], d["side"], d["penalty"], d["paid"], d["reputation"]), ("bob", "buyer", 24.0, 10.0, 0.8))
        self.assertEqual(nxt["firms"]["bob"]["cash"], 0.0)
        self.assertEqual(nxt["firms"]["ann"]["cash"], 1010.0)
        self.assertEqual(nxt["firms"]["ann"]["inventory"]["parts"], 4)
        self.assertEqual(nxt["firms"]["bob"]["reputation"], 0.8)

    def test_seller_default_and_reputation_floor(self):
        firms = {"ann": make_firm(self.rules, reputation=0.1), "bob": make_firm(self.rules)}
        state = self.state_with(3, firms, contracts_open=[self.contract(3)])
        result, nxt = self.resolve(state, {"ann": {}, "bob": {}})
        self.assertEqual(result["deliveries"][0]["status"], "seller_default")
        self.assertEqual(nxt["firms"]["ann"]["cash"], 976.0)
        self.assertEqual(nxt["firms"]["bob"]["cash"], 1024.0)
        self.assertEqual(nxt["firms"]["ann"]["reputation"], 0.0)

    def test_offer_publish_accept_taken_and_expiry(self):
        firms = {n: make_firm(self.rules) for n in ("ann", "bob", "cat")}
        state = self.state_with(1, firms)
        offer = {"id": "ann-1", "deliver": "parts", "qty": 2, "price": 30.0, "due": 3}
        result, s2 = self.resolve(state, {"ann": {"offers": [offer, dict(offer, id="ann-2")]}, "bob": {}, "cat": {}})
        self.assertEqual([o["id"] for o in result["offers"]], ["ann-1", "ann-2"])
        self.assertEqual(s2["firms"]["ann"]["offer_seq"], 2)
        result, s3 = self.resolve(s2, {"ann": {"accept": ["ann-1"]}, "bob": {"accept": ["ann-1"]}, "cat": {"accept": ["ann-1"]}})
        self.assertEqual([(c["buyer"], c["id"]) for c in result["contracts"]["accepted"]], [("bob", "ann-1")])
        self.assertEqual([(r["firm"], r["reason"]) for r in result["contracts"]["rejected"]], [("cat", "taken")])
        self.assertIn("accept[0]", [p["where"] for p in result["invalid"]["ann"]])
        self.assertEqual(result["contracts"]["expired"], ["ann-2"])
        self.assertEqual(s3["offers_open"], [])
        self.assertEqual(len(s3["contracts_open"]), 1)
        result, s4 = self.resolve(s3, {"ann": {"accept": ["ann-2"]}, "bob": {}, "cat": {}})
        self.assertEqual(result["invalid"]["ann"][0]["reason"], "no open offer 'ann-2'")

    def test_offer_validation(self):
        firms = {"ann": make_firm(self.rules, offer_seq=3)}
        state = self.state_with(2, firms)
        clean, problems, fatal = market.validate_move(self.match, state, 2, "ann", envelope(self.match, 2, "ann", offers=[
            {"id": "ann-3", "deliver": "ore", "qty": 1, "price": 1.0, "due": 4},
            {"id": "bob-9", "deliver": "ore", "qty": 1, "price": 1.0, "due": 4},
            {"id": "ann-4", "deliver": "ore", "qty": 1, "price": 1.0, "due": 3},
            {"id": "ann-4", "deliver": "ore", "qty": 1, "price": 1.0, "due": 7},
            {"id": "ann-4", "deliver": "ore", "qty": 1, "price": 1.0, "due": 4},
        ]), self.players)
        self.assertFalse(fatal)
        self.assertEqual([o["id"] for o in clean["offers"]], ["ann-4"])
        self.assertEqual([p["where"] for p in problems], ["offers[0]", "offers[1]", "offers[2]", "offers[3]"])

    def test_reservation_drops_the_right_orders(self):
        firms = {"ann": make_firm(self.rules, cash=100.0, inventory={"ore": 10})}
        state = self.state_with(1, firms)
        move = envelope(self.match, 1, "ann", orders=[
            {"side": "buy", "good": "grain", "qty": 10, "limit": 5.0},
            {"side": "buy", "good": "grain", "qty": 20, "limit": 5.0},
            {"side": "buy", "good": "fuel", "qty": 5, "limit": 5.0},
            {"side": "sell", "good": "ore", "qty": 8, "limit": 1.0},
            {"side": "sell", "good": "ore", "qty": 3, "limit": 1.0},
            {"side": "sell", "good": "ore", "qty": 2, "limit": 1.0},
        ])
        clean, problems, fatal = market.validate_move(self.match, state, 1, "ann", move, self.players)
        self.assertFalse(fatal)
        self.assertEqual([o["seq"] for o in clean["orders"]], [0, 2, 3, 5])
        self.assertEqual([p["where"] for p in problems], ["orders[1]", "orders[4]"])
        move = envelope(self.match, 1, "ann", build={"farm": 1, "mine": 1}, orders=[{"side": "buy", "good": "grain", "qty": 1, "limit": 1.0}])
        clean, problems, fatal = market.validate_move(self.match, state, 1, "ann", move, self.players)
        self.assertEqual(clean["build"], {"farm": 1})
        self.assertEqual(clean["orders"], [])
        self.assertEqual([p["where"] for p in problems], ["build.mine", "orders[0]"])

    def test_negative_cash_cannot_buy_or_build_but_can_sell(self):
        firms = {"ann": make_firm(self.rules, cash=5.0, facilities={"mine": 1}, inventory={"ore": 6})}
        state = self.state_with(1, firms)
        move = envelope(self.match, 1, "ann", build={"farm": 1}, orders=[
            {"side": "buy", "good": "grain", "qty": 1, "limit": 0.5},
            {"side": "sell", "good": "ore", "qty": 6, "limit": 1.0}])
        clean, problems, fatal = market.validate_move(self.match, state, 1, "ann", move, self.players)
        self.assertEqual(clean["build"], {})
        self.assertEqual([o["side"] for o in clean["orders"]], ["sell"])
        self.assertEqual(len(problems), 2)
        result, nxt = self.resolve(state, {"ann": {"orders": [{"side": "sell", "good": "ore", "qty": 6, "limit": 1.0}]}})
        self.assertEqual(result["opex"]["ann"], 10.0)
        self.assertEqual(result["trades"]["ann"]["ore"]["sold"], 6)
        self.assertGreater(nxt["firms"]["ann"]["cash"], 5.0 - 10.0)

    def test_invalid_move_files_are_reported_and_do_nothing(self):
        firms = {n: make_firm(self.rules, inventory={"ore": 5}) for n in ("ann", "bob", "cat")}
        state = self.state_with(2, firms)
        sell = {"side": "sell", "good": "ore", "qty": 5, "limit": 1.0}
        texts = {
            "ann": "{not json",
            "bob": text(envelope(self.match, 3, "bob", orders=[sell])),
            "cat": text(envelope(self.match, 2, "ann", orders=[sell])),
            "dan": text(envelope(self.match, 2, "dan", orders=[sell])),
            "..": text(envelope(self.match, 2, "..", orders=[sell])),
        }
        result, nxt = market.resolve_round(self.match, state, texts, self.players)
        self.assertEqual(sorted(result["invalid"]), ["..", "ann", "bob", "cat", "dan"])
        self.assertEqual(result["trades"], {})
        self.assertEqual(sorted(nxt["firms"]), ["ann", "bob", "cat"])
        self.assertEqual(result["moved"], ["ann", "bob", "cat"])
        bad = envelope(self.match, 2, "ann", orders=[
            {"side": "sell", "good": "ore", "qty": True, "limit": 1.0},
            {"side": "sell", "good": "ore", "qty": -1, "limit": 1.0},
            {"side": "sell", "good": "ore", "qty": 1, "limit": float("nan")},
            {"side": "sell", "good": "ore", "qty": 1, "limit": float("inf")},
            {"side": "sell", "good": "gold", "qty": 1, "limit": 1.0},
            {"side": "sell", "good": "ore", "qty": 10 ** 9, "limit": 1.0},
            {"side": "sell", "good": "ore", "qty": 1, "limit": 0.001},
            "not an order",
            {"side": "sell", "good": "ore", "qty": 1, "limit": 1.0},
        ], build={"castle": 1, "farm": -2}, run={"farm": "all"}, accept=["x", "x", 3], extra=1)
        clean, problems, fatal = market.validate_move(self.match, state, 2, "ann", bad, self.players)
        self.assertFalse(fatal)
        self.assertEqual(len(clean["orders"]), 1)
        self.assertEqual(clean["orders"][0]["seq"], 8)
        self.assertEqual(clean["build"], {})
        self.assertEqual(clean["accept"], [])
        self.assertEqual(len(problems), 15)
        many = envelope(self.match, 2, "ann", orders=[{"side": "buy", "good": "ore", "qty": 1, "limit": 0.01}] * 41)
        clean, problems, fatal = market.validate_move(self.match, state, 2, "ann", many, self.players)
        self.assertEqual(len(clean["orders"]), 40)
        for fatal_obj in ([], "x", 3, None):
            _c, problems, fatal = market.validate_move(self.match, state, 2, "ann", fatal_obj, self.players)
            self.assertTrue(fatal)
        self.assertEqual(market.parse_move("x" * 70000)[1], "file larger than 65536 bytes")

    def test_contract_cap_refuses_a_sixth_contract_for_either_side(self):
        firms = {n: make_firm(self.rules) for n in ("ann", "bob", "cat")}
        five = [dict(self.contract(due=6), id="ann-%d" % i, buyer="cat") for i in range(1, 6)]
        offer = {"id": "ann-6", "seller": "ann", "deliver": "parts", "qty": 1, "price": 10.0, "due": 6, "offered": 1}
        state = self.state_with(2, firms, contracts_open=five, offers_open=[offer])
        result, _ = self.resolve(state, {"bob": {"accept": ["ann-6"]}})
        self.assertEqual(result["contracts"]["accepted"], [])
        self.assertEqual(result["contracts"]["rejected"][0]["reason"], "seller already has 5 open contracts")
        five = [dict(self.contract(due=6), id="cat-%d" % i, seller="cat", buyer="bob") for i in range(1, 6)]
        state = self.state_with(2, firms, contracts_open=five, offers_open=[offer])
        result, _ = self.resolve(state, {"bob": {"accept": ["ann-6"]}})
        self.assertEqual(result["contracts"]["rejected"][0]["reason"], "buyer already has 5 open contracts")

    def test_both_sides_default_pay_what_they_have(self):
        firms = {"ann": make_firm(self.rules, cash=10.0), "bob": make_firm(self.rules, cash=5.0),
                 "cat": make_firm(self.rules)}
        state = self.state_with(3, firms, contracts_open=[self.contract(due=3)])  # 4 parts at 30: value 120
        result, nxt = self.resolve(state, {})
        self.assertEqual(result["deliveries"][0]["status"], "both_default")
        self.assertEqual([d["side"] for d in result["defaults"]], ["seller", "buyer"])
        # the penalty is 24 each way; ann pays the 10 it has, then bob pays the 15 it now holds
        self.assertAlmostEqual(nxt["firms"]["ann"]["cash"], 15.0)
        self.assertAlmostEqual(nxt["firms"]["bob"]["cash"], 0.0)
        self.assertAlmostEqual(nxt["firms"]["ann"]["reputation"], 0.8)
        self.assertAlmostEqual(nxt["firms"]["bob"]["reputation"], 0.8)

    def test_sell_eaten_by_production_is_dropped_at_clearing(self):
        self.rules["p_disaster"] = 0.0
        firms = {"ann": make_firm(self.rules, cash=500.0, facilities={"factory": 1},
                                  inventory={"ore": 8, "fuel": 4, "grain": 1}),
                 "bob": make_firm(self.rules)}
        state = self.state_with(2, firms)
        result, nxt = self.resolve(state, {"ann": {"orders": [{"side": "sell", "good": "ore", "qty": 8, "limit": 1.0}]}})
        reasons = [p["reason"] for p in result["invalid"]["ann"]]
        self.assertTrue(any("after production and deliveries" in r for r in reasons), reasons)
        self.assertEqual(nxt["firms"]["ann"]["inventory"]["parts"], 4)
        self.assertEqual(nxt["firms"]["ann"]["inventory"]["ore"], 0)

    def test_buy_is_dropped_at_clearing_after_a_penalty(self):
        firms = {"ann": make_firm(self.rules, inventory={"parts": 4}), "bob": make_firm(self.rules, cash=30.0),
                 "cat": make_firm(self.rules)}
        state = self.state_with(3, firms, contracts_open=[self.contract(due=3)])
        result, nxt = self.resolve(state, {"bob": {"orders": [{"side": "buy", "good": "ore", "qty": 5, "limit": 5.0}]}})
        self.assertEqual(result["deliveries"][0]["status"], "buyer_default")
        reasons = [p["reason"] for p in result["invalid"]["bob"]]
        self.assertTrue(any("cash after deliveries and penalties is 6.00" in r for r in reasons), reasons)

    def test_standings_tie_is_broken_by_name(self):
        firms = {n: make_firm(self.rules) for n in ("cat", "ann", "bob")}
        result, _ = self.resolve(self.state_with(2, firms), {})
        self.assertEqual([s["player"] for s in result["standings"]], ["ann", "bob", "cat"])
        self.assertEqual(len({s["score"] for s in result["standings"]}), 1)

    def test_pool_above_its_start_does_not_regenerate(self):
        firms = {"ann": make_firm(self.rules)}
        result, nxt = self.resolve(self.state_with(2, firms, pools={"ore": 3100, "fuel": 1990}), {})
        self.assertEqual(nxt["pools"], {"ore": 3100, "fuel": 2000})

    def test_net_worth_formula(self):
        firm = make_firm(self.rules, cash=500.0, inventory={"ore": 10}, pending_builds={"farm": 1})
        state = self.state_with(1, {"ann": firm})
        result, nxt = self.resolve(state, {"ann": {}})
        # the pending farm comes online this round and makes 8 grain (valued at Pmax/2 = 2.5):
        # 500 cash + 10 ore x 4.00 + 8 grain x 2.50 + one farm at 0.8 x 100
        self.assertEqual(result["net_worth"]["ann"], 640.0)
        self.assertNotIn("ann", result["opex"])
        result, nxt2 = self.resolve(nxt, {"ann": {}})
        self.assertEqual(result["opex"]["ann"], 8.0)
        self.assertEqual(nxt2["firms"]["ann"]["inventory"]["grain"], 16)
        self.assertEqual(result["net_worth"]["ann"], 652.0)
        self.assertEqual(nxt2["firms"]["ann"]["net_worth_history"], [640.0, 652.0])

    def test_max_drawdown_and_score(self):
        self.assertEqual(market.max_drawdown([100, 120, 90, 130, 70, 110]), 60)
        self.assertEqual(market.max_drawdown([1, 2, 3]), 0)
        self.assertEqual(market.max_drawdown([]), 0)
        firm = make_firm(self.rules, net_worth_history=[1000.0, 1300.0, 900.0])
        state = self.state_with(4, {"ann": firm})
        result, _ = self.resolve(state, {"ann": {}})
        self.assertEqual(result["net_worth"]["ann"], 1000.0)
        self.assertEqual(result["drawdown"]["ann"], 400.0)
        self.assertEqual(result["scores"]["ann"], 800.0)
        self.assertEqual(result["standings"][0]["player"], "ann")

    def test_builds_charged_then_online_and_valued(self):
        state = self.state_with(1, {"ann": make_firm(self.rules)})
        result, s2 = self.resolve(state, {"ann": {"build": {"mine": 2, "farm": 1}}})
        self.assertEqual(result["builds"]["ann"], {"farm": 1, "mine": 2})
        self.assertEqual(s2["firms"]["ann"]["cash"], 660.0)
        self.assertEqual(s2["firms"]["ann"]["pending_builds"]["mine"], 2)
        self.assertEqual(result["net_worth"]["ann"], 660.0 + 0.8 * 340)
        result, s3 = self.resolve(s2, {"ann": {}})
        self.assertEqual(s3["firms"]["ann"]["facilities"], {"farm": 1, "mine": 2, "well": 0, "factory": 0})
        self.assertEqual(result["production"]["ann"]["made"], {"grain": 8, "ore": 12})
        self.assertNotIn("ann", result["opex"], "opex is charged before builds come online")
        result, s4 = self.resolve(s3, {"ann": {}})
        self.assertEqual(result["opex"]["ann"], 28.0)

    def test_clearing_updates_last_price_and_moves_inventory(self):
        firms = {"ann": make_firm(self.rules, inventory={"grain": 20}), "bob": make_firm(self.rules)}
        state = self.state_with(4, firms)
        result, nxt = self.resolve(state, {
            "ann": {"orders": [{"side": "sell", "good": "grain", "qty": 20, "limit": 2.0}]},
            "bob": {"orders": [{"side": "buy", "good": "grain", "qty": 5, "limit": 6.0}]}})
        p = result["prices"]["grain"]
        self.assertEqual(p["volume"], 20)
        # the 20th bid unit is on the consumers' 3.50 step; midpoint with the 2.00 ask
        self.assertEqual(p["price"], 2.75)
        self.assertEqual(result["trades"]["bob"]["grain"]["bought"], 5)
        self.assertEqual(result["trades"]["ann"]["grain"]["sold"], 20)
        self.assertEqual(p["consumers_bought"], 15)
        self.assertEqual(nxt["last_price"]["grain"], 2.75)
        self.assertEqual(nxt["firms"]["bob"]["cash"], 1000.0 - 13.75)
        self.assertEqual(nxt["firms"]["ann"]["cash"], 1055.0)
        self.assertEqual(nxt["firms"]["bob"]["inventory"]["grain"], 5)
        self.assertIsNone(nxt["last_price"]["ore"])

    def test_events_reproducible_from_seed(self):
        state = self.state_with(1, {"ann": make_firm(self.rules, facilities={"mine": 1}, inventory={"grain": 5})})
        texts = {"ann": text(envelope(self.match, 1, "ann"))}
        a, na = market.resolve_round(self.match, state, texts, self.players)
        b, nb = market.resolve_round(self.match, state, texts, self.players)
        self.assertEqual(market.dumps(a), market.dumps(b))
        self.assertEqual(market.dumps(na), market.dumps(nb))
        expected = market.round_seed("test", 1, texts)
        self.assertEqual(a["seed"], expected)
        rng = random.Random(int(expected, 16))
        self.assertEqual(a["dice"], [round(rng.random(), 9) for _ in range(3)])
        seen = set()
        for i in range(400):
            match = make_match(seed="probe-%d" % i)
            res, nxt = market.resolve_round(match, state, texts, self.players)
            for e in res["events"]:
                seen.add(e["event"])
                if e["event"] == "disaster" and e["facility"] == "mine":
                    self.assertEqual(res["production"]["ann"]["idle"]["mine"], 1)
                if e["event"] == "demand_shock":
                    self.assertEqual(nxt["shocks"][e["good"]], [e["factor"], 1])
                    self.assertTrue(0.5 <= e["factor"] <= 2.0)
                    res2, nxt2 = market.resolve_round(make_match(seed="never-%d" % i), nxt, {}, self.players)
                    if not any(x["event"] == "demand_shock" and x["good"] == e["good"] for x in res2["events"]):
                        self.assertEqual(nxt2["shocks"][e["good"]], [1.0, 0])
                if e["event"] == "windfall":
                    self.assertEqual(res["pools"][e["pool"]] - 200, nxt["pools"][e["pool"]] - 200)
            if seen == {"disaster", "demand_shock", "windfall"}:
                break
        self.assertEqual(seen, {"disaster", "demand_shock", "windfall"})

    def test_bots_write_valid_moves(self):
        state = self.state_with(1, {})
        for style in ("merchant", "hoarder"):
            move = market.bot_move(self.match, state, 1, "ann", style)
            clean, problems, fatal = market.validate_move(self.match, state, 1, "ann", move, self.players)
            self.assertEqual(problems, [])
            self.assertTrue(clean["build"])
        rich = make_firm(self.rules, cash=900.0, facilities={"farm": 1, "mine": 1, "well": 1, "factory": 1},
                         inventory={"ore": 20, "grain": 30, "fuel": 9, "parts": 8})
        state = self.state_with(12, {"ann": rich, "bob": make_firm(self.rules, inventory={"ore": 50})},
                                last_price={"ore": 2.0, "grain": 3.0, "fuel": 5.0, "parts": 30.0})
        for name, style in (("ann", "merchant"), ("bob", "hoarder")):
            move = market.bot_move(self.match, state, 12, name, style)
            clean, problems, fatal = market.validate_move(self.match, state, 12, name, move, self.players)
            self.assertEqual(problems, [])
        self.assertTrue(any(o["side"] == "sell" and o["good"] == "ore" for o in move["orders"]))

    def test_differences_tolerance(self):
        self.assertEqual(market.differences({"a": [1.0, 2]}, {"a": [1.0 + 5e-9, 2]}), [])
        self.assertEqual(len(market.differences({"a": 1}, {"a": 2})), 1)
        self.assertEqual(len(market.differences({"a": 1.0}, {"a": 1.1})), 1)
        self.assertEqual(len(market.differences({"a": None}, {"a": 0})), 1)
        self.assertEqual(len(market.differences([1], [1, 2])), 1)


class CommandTests(unittest.TestCase):
    """The CLI on a small match in a temporary directory."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = str(Path(self.tmp.name) / "003-test")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                market.main(list(args))
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
        return code, out.getvalue() + err.getvalue()

    def play(self, rounds, names=("mer-a", "hoard-b"), upto=None):
        self.assertEqual(self.run_cli("new", self.dir, "--seed", "s", "--rounds", str(rounds))[0], 0)
        for n in names:
            self.assertEqual(self.run_cli("join", self.dir, "--player", n)[0], 0)
        for rnd in range(1, (upto or rounds) + 1):
            for n in names:
                style = "hoarder" if n.startswith("hoard") else "merchant"
                code, text_out = self.run_cli("bot", self.dir, str(rnd), "--player", n, "--style", style)
                self.assertEqual(code, 0, text_out)
            code, text_out = self.run_cli("resolve", self.dir, str(rnd))
            self.assertEqual(code, 0, text_out)

    def test_whole_match_resolves_verifies_and_renders(self):
        self.play(4)
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("match complete", out)
        final = json.loads((Path(self.dir) / "rounds" / "004" / "result.json").read_text())
        self.assertTrue(final["final"])
        self.assertEqual([s["player"] for s in final["standings"]], sorted(final["scores"], key=lambda n: (-final["scores"][n], n)))
        self.assertTrue((Path(self.dir) / "rounds" / "005" / "state.json").exists())
        code, out = self.run_cli("score", self.dir)
        self.assertEqual(code, 0)
        self.assertIn("(final)", out)
        code, svg = self.run_cli("render", self.dir)
        self.assertEqual(code, 0)
        root = ET.fromstring(svg)
        tags = {el.tag.split("}")[-1] for el in root.iter()}
        self.assertFalse(tags & {"script", "image", "use", "foreignObject"})
        for el in root.iter():
            for attr, value in el.attrib.items():
                self.assertNotIn("http", value if attr != "xmlns" else "")
        self.assertIn("mer-a", svg)
        code, out = self.run_cli("book", self.dir, "4")
        self.assertEqual(code, 0)
        self.assertIn("would clear", out)
        for rnd in range(1, 5):
            code, out = self.run_cli("resolve", self.dir, "%03d" % rnd, "--check")
            self.assertEqual(code, 0, out)
        committed = (Path(self.dir) / "rounds" / "002" / "result.json").read_text()
        self.assertTrue(committed.endswith("}\n"))
        self.assertEqual(json.dumps(json.loads(committed), sort_keys=True, indent=2, ensure_ascii=False) + "\n", committed)

    def test_verify_detects_a_tampered_result(self):
        self.play(2)
        path = Path(self.dir) / "rounds" / "002" / "result.json"
        result = json.loads(path.read_text())
        result["net_worth"]["mer-a"] += 1
        path.write_text(market.dumps(result))
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 1)
        self.assertIn("round 002", out)
        self.assertIn("net_worth", out)

    def test_never_overwrite(self):
        self.play(3, upto=1)
        code, out = self.run_cli("new", self.dir, "--seed", "s")
        self.assertEqual(code, 1)
        self.assertIn("never overwrites", out)
        code, out = self.run_cli("join", self.dir, "--player", "mer-a")
        self.assertEqual(code, 1)
        code, out = self.run_cli("resolve", self.dir, "1")
        self.assertEqual(code, 1)
        self.assertIn("exists", out)
        code, out = self.run_cli("bot", self.dir, "2", "--player", "mer-a")
        self.assertEqual(code, 0)
        code, out = self.run_cli("bot", self.dir, "2", "--player", "mer-a")
        self.assertEqual(code, 1)
        code, out = self.run_cli("bot", self.dir, "2", "--player", "mer-a", "--force")
        self.assertEqual(code, 0)
        code, out = self.run_cli("bot", self.dir, "1", "--player", "mer-a", "--force")
        self.assertEqual(code, 1)
        self.assertIn("already resolved", out)

    def test_allow_absent(self):
        self.play(3, upto=1)
        code, out = self.run_cli("bot", self.dir, "2", "--player", "mer-a")
        self.assertEqual(code, 0)
        code, out = self.run_cli("resolve", self.dir, "2")
        self.assertEqual(code, 1)
        self.assertIn("hoard-b", out)
        code, out = self.run_cli("resolve", self.dir, "2", "--allow-absent")
        self.assertEqual(code, 0, out)
        result = json.loads((Path(self.dir) / "rounds" / "002" / "result.json").read_text())
        self.assertEqual(result["absent"], ["hoard-b"])
        self.assertEqual(result["moved"], ["mer-a"])
        self.assertIn("hoard-b", result["production"])
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 0, out)

    def test_late_join_waits_until_it_moves_and_never_blocks(self):
        self.play(4, upto=2)
        code, out = self.run_cli("join", self.dir, "--player", "late-c")
        self.assertEqual(code, 0)
        player = json.loads((Path(self.dir) / "players" / "late-c.json").read_text())
        self.assertEqual(player["joined"], 3)
        for n in ("mer-a", "hoard-b"):
            self.assertEqual(self.run_cli("bot", self.dir, "3", "--player", n)[0], 0)
        # a joined player that has not moved does not block the round and is not absent
        code, out = self.run_cli("resolve", self.dir, "3")
        self.assertEqual(code, 0, out)
        result = json.loads((Path(self.dir) / "rounds" / "003" / "result.json").read_text())
        self.assertEqual(result["waiting"], ["late-c"])
        self.assertEqual(result["absent"], [])
        self.assertEqual(result["joined"], [])
        state4 = json.loads((Path(self.dir) / "rounds" / "004" / "state.json").read_text())
        self.assertNotIn("late-c", state4["firms"])
        for n in ("mer-a", "hoard-b", "late-c"):
            self.assertEqual(self.run_cli("bot", self.dir, "4", "--player", n)[0], 0)
        code, out = self.run_cli("resolve", self.dir, "4")
        self.assertEqual(code, 0, out)
        result = json.loads((Path(self.dir) / "rounds" / "004" / "result.json").read_text())
        self.assertEqual(result["joined"], ["late-c"])
        self.assertEqual(result["waiting"], [])
        state5 = json.loads((Path(self.dir) / "rounds" / "005" / "state.json").read_text())
        self.assertIn("late-c", state5["firms"])
        self.assertEqual(len(state5["firms"]["late-c"]["net_worth_history"]), 1)
        self.assertEqual(len(state5["firms"]["mer-a"]["net_worth_history"]), 4)
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 0, out)

    def test_book_command_prints_ladders_and_a_clearing(self):
        self.play(3, upto=1)
        for n in ("mer-a", "hoard-b"):
            self.assertEqual(self.run_cli("bot", self.dir, "2", "--player", n)[0], 0)
        code, out = self.run_cli("book", self.dir, "2")
        self.assertEqual(code, 0, out)
        for g in GOODS:
            self.assertIn("\n%s  (consumers want" % g, out)
        self.assertIn("bids:", out)
        self.assertIn("asks:", out)
        self.assertIn("would clear", out)

    def test_join_refuses_bad_names_and_finished_matches(self):
        self.play(1)
        for bad in ("Bad", "a", "x" * 33, "../x", "a_b", "_consumers"):
            code, out = self.run_cli("join", self.dir, "--player", bad)
            self.assertEqual(code, 1, bad)
        code, out = self.run_cli("join", self.dir, "--player", "too-late")
        self.assertEqual(code, 1)
        self.assertIn("no open round", out)

    def test_validate_command(self):
        self.play(3, upto=1)
        moves = Path(self.dir) / "rounds" / "002" / "moves"
        moves.mkdir(parents=True, exist_ok=True)
        good = moves / "mer-a.json"
        good.write_text(market.dumps({"game": market.VERSION, "match": "003-test", "round": 2, "player": "mer-a"}))
        code, out = self.run_cli("validate", self.dir, "2", str(good))
        self.assertEqual(code, 0, out)
        self.assertIn("ok", out)
        bad = moves / "hoard-b.json"
        bad.write_text(market.dumps({"game": market.VERSION, "match": "003-test", "round": 2, "player": "hoard-b",
                                     "orders": [{"side": "sell", "good": "ore", "qty": 999, "limit": 1.0}]}))
        code, out = self.run_cli("validate", self.dir, "2", str(bad))
        self.assertEqual(code, 1)
        self.assertIn("orders[0]", out)
        bad.write_text("{{{")
        code, out = self.run_cli("validate", self.dir, "2", str(bad))
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", out)
        stranger = moves / "nobody-x.json"
        stranger.write_text(market.dumps({"game": market.VERSION, "match": "003-test", "round": 2, "player": "nobody-x"}))
        code, out = self.run_cli("validate", self.dir, "2", str(stranger))
        self.assertEqual(code, 1)
        self.assertIn("no players/nobody-x.json", out)
        code, out = self.run_cli("resolve", self.dir, "2", "--allow-absent")
        self.assertEqual(code, 0, out)
        result = json.loads((Path(self.dir) / "rounds" / "002" / "result.json").read_text())
        self.assertEqual(sorted(result["invalid"]), ["hoard-b", "nobody-x"])
        self.assertEqual(result["moved"], ["hoard-b", "mer-a"])
        self.assertNotIn("nobody-x", json.loads((Path(self.dir) / "rounds" / "003" / "state.json").read_text())["firms"])

    def test_new_writes_the_documented_defaults(self):
        self.assertEqual(self.run_cli("new", self.dir, "--seed", "opening-bell")[0], 0)
        match = json.loads((Path(self.dir) / "match.json").read_text())
        self.assertEqual(match["rounds"], 24)
        self.assertEqual(match["rules"], market.default_rules())
        state = json.loads((Path(self.dir) / "rounds" / "001" / "state.json").read_text())
        self.assertEqual(state, market.initial_state(match))
        self.assertEqual(state["pools"], {"ore": 3000, "fuel": 2000})


if __name__ == "__main__":
    unittest.main()
