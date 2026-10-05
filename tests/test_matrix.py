"""Tests for made/matrix.py, the Matrix referee.

Run with: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_matrix -v
"""
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
import matrix  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SEATS = matrix.SEATS


def fresh(seed="test", order_rounds=4, names=("ann", "bob", "cy", "dee")):
    """A match and its round-1 state, with the given names seated a, b, c, d
    (None leaves a seat empty)."""
    match, state = matrix.new_match("t-match", seed, order_rounds)
    seats = {s: (names[i] if i < len(names) else None) for i, s in enumerate(SEATS)}
    state["seats"] = dict(seats)
    return match, state, seats


def engine_move(seat, commit=None, reveal=None, stance=None, pacts=None, say=None):
    """The engine's view of a valid move file (what check_move returns)."""
    return {"seat": seat, "commit": commit, "reveal": reveal, "stance": dict(stance or {}),
            "pacts": sorted(pacts or []), "say": say}


def rng_for(text="dice"):
    return random.Random(int(matrix.sha256_text(text), 16))


def envelope(match, state, player, **fields):
    move = {"game": matrix.VERSION, "match": match["match"], "round": state["round"], "player": player}
    move.update(fields)
    return move


def neutral_with_three_neighbours(match):
    """A non-home territory with at least three neighbours, and three of them."""
    adj = matrix.adjacency(match["map"])
    for tid in sorted(adj):
        if match["map"]["territories"][tid]["home"] is None and len(adj[tid]) >= 3:
            return tid, adj[tid][:3]
    return None, None


class MapTests(unittest.TestCase):
    def test_map_is_deterministic_from_the_seed(self):
        a = matrix.generate_map("cold-open", matrix.DEFAULT_RULES)
        b = matrix.generate_map("cold-open", matrix.DEFAULT_RULES)
        self.assertEqual(a, b)
        c = matrix.generate_map("another", matrix.DEFAULT_RULES)
        self.assertNotEqual(a, c)

    def test_map_shape_homes_never_adjacent(self):
        for i in range(60):
            gmap = matrix.generate_map("seed-%d" % i, matrix.DEFAULT_RULES)
            terr = gmap["territories"]
            self.assertEqual(len(terr), 12)
            self.assertEqual(len(gmap["edges"]), 12 + matrix.DEFAULT_RULES["chords"])
            self.assertEqual(sum(t["yield"] for t in terr.values()), 4 * 3 + 16)
            homes = {tid for tid, t in terr.items() if t["home"]}
            self.assertEqual(sorted(terr[t]["home"] for t in homes), SEATS)
            adj = matrix.adjacency(gmap)
            for tid, ns in adj.items():
                self.assertTrue(2 <= len(ns) <= 4, (tid, ns))
                if tid in homes:
                    self.assertFalse(any(n in homes for n in ns), "homes %s and %s are adjacent" % (tid, ns))
            seen, stack = set(), ["t01"]
            while stack:
                t = stack.pop()
                if t not in seen:
                    seen.add(t)
                    stack.extend(adj[t])
            self.assertEqual(len(seen), 12)
            self.assertEqual(gmap["edges"], sorted(gmap["edges"]))
            chords = [(int(a[1:]) - 1, int(b[1:]) - 1) for a, b in gmap["edges"]
                      if not ((int(b[1:]) - int(a[1:])) == 1 or (a == "t01" and b == "t12"))]
            for x in chords:
                for y in chords:
                    self.assertFalse(matrix.chords_cross(x, y), (x, y))

    def test_new_match_writes_documented_defaults(self):
        match, state = matrix.new_match("m", "cold-open", 16)
        self.assertEqual(match["rounds"], 17)
        self.assertEqual(match["order_rounds"], 16)
        self.assertEqual(match["rules"], matrix.DEFAULT_RULES)
        for seat in SEATS:
            home = matrix.home_of_seat(match["map"], seat)
            self.assertEqual(state["territories"][home], {"holder": seat, "units": 6})
            self.assertEqual(state["powers"][seat]["resources"], 5)
            self.assertEqual(state["powers"][seat]["reputation"], 1.0)
            self.assertEqual(state["scores"][seat], 3 + 5 + 6)
        neutral = [t for t in state["territories"].values() if t["holder"] is None]
        self.assertEqual(len(neutral), 8)
        self.assertTrue(all(t["units"] == 0 for t in neutral))


class CommitRevealTests(unittest.TestCase):
    def setUp(self):
        self.match, self.state, self.seats = fresh()
        self.home_a = matrix.home_of_seat(self.match["map"], "a")
        self.orders = {"recruit": {self.home_a: 1}}
        self.nonce = "ab" * 16
        self.state["round"] = 2
        self.state["powers"]["a"]["commit"] = matrix.commit_hash(self.orders, self.nonce)

    def test_commit_hash_is_sha256_of_canonical_orders_newline_nonce(self):
        import hashlib
        text = matrix.canonical(self.orders) + "\n" + self.nonce
        self.assertEqual(matrix.commit_hash(self.orders, self.nonce), hashlib.sha256(text.encode()).hexdigest())

    def test_round_trip_applies_the_orders(self):
        moves = {"a": engine_move("a", reveal={"orders": self.orders, "nonce": self.nonce})}
        nxt, out = matrix.simulate_round(self.state, self.match, self.seats, moves, rng_for())
        self.assertEqual(out["reveals"]["a"]["status"], "applied")
        self.assertEqual(nxt["territories"][self.home_a]["units"], 7)
        self.assertEqual(nxt["powers"]["a"]["reputation"], 1.0)
        self.assertEqual(nxt["powers"]["a"]["commit"], None)

    def test_tampered_reveal_is_void_and_costs_reputation(self):
        tampered = {"recruit": {self.home_a: 2}}
        moves = {"a": engine_move("a", reveal={"orders": tampered, "nonce": self.nonce})}
        nxt, out = matrix.simulate_round(self.state, self.match, self.seats, moves, rng_for())
        self.assertEqual(out["reveals"]["a"]["status"], "broken_commit")
        self.assertEqual(nxt["territories"][self.home_a]["units"], 6)
        self.assertEqual(nxt["powers"]["a"]["reputation"], 0.75)
        self.assertEqual(nxt["powers"]["a"]["broken_commits"], 1)
        self.assertIn({"kind": "broken_commit", "seat": "a", "reputation": 0.75}, out["events"])
        wrong_nonce = {"a": engine_move("a", reveal={"orders": self.orders, "nonce": "cd" * 16})}
        _n, out = matrix.simulate_round(self.state, self.match, self.seats, wrong_nonce, rng_for())
        self.assertEqual(out["reveals"]["a"]["status"], "broken_commit")

    def test_missing_reveal_after_a_commit_is_no_reveal(self):
        moves = {"a": engine_move("a", commit="0" * 64)}
        nxt, out = matrix.simulate_round(self.state, self.match, self.seats, moves, rng_for())
        self.assertEqual(out["reveals"]["a"]["status"], "no_reveal")
        self.assertEqual(nxt["powers"]["a"]["reputation"], 0.75)
        self.assertEqual(nxt["powers"]["a"]["commit"], "0" * 64)
        _n, out = matrix.simulate_round(self.state, self.match, self.seats, {}, rng_for())
        self.assertEqual(out["reveals"]["a"]["status"], "no_reveal")
        self.assertEqual(out["reveals"]["b"]["status"], "absent")

    def test_reputation_has_a_floor_of_zero(self):
        self.state["powers"]["a"]["reputation"] = 0.25
        nxt, _o = matrix.simulate_round(self.state, self.match, self.seats, {}, rng_for())
        self.assertEqual(nxt["powers"]["a"]["reputation"], 0.0)
        nxt["powers"]["a"]["commit"] = "1" * 64
        nxt2, _o = matrix.simulate_round(nxt, self.match, self.seats, {}, rng_for())
        self.assertEqual(nxt2["powers"]["a"]["reputation"], 0.0)


class BattleTests(unittest.TestCase):
    """Hand-made round-2 states with the orders already committed."""

    def setUp(self):
        self.match, self.state, self.seats = fresh()
        self.adj = matrix.adjacency(self.match["map"])
        self.terr = self.state["territories"]
        self.state["round"] = 2
        self.state["pacts_active"] = []
        for tid in self.terr:
            self.terr[tid] = {"holder": None, "units": 0}

    def commit(self, seat, orders, nonce="11"):
        self.state["powers"][seat]["commit"] = matrix.commit_hash(orders, nonce)
        return engine_move(seat, reveal={"orders": orders, "nonce": nonce})

    def pair(self):
        """Two adjacent territories (x held by a, y by b) and a neutral z next to x."""
        for x in sorted(self.adj):
            ys = self.adj[x]
            if len(ys) >= 2:
                return x, ys[0], ys[1]
        self.fail("no territory with two neighbours")

    def resolve(self, moves, rng=None):
        return matrix.simulate_round(self.state, self.match, self.seats, moves, rng or rng_for())

    def test_moves_clip_to_the_units_present_in_file_order(self):
        x, y, z = self.pair()
        self.terr[x] = {"holder": "a", "units": 5}
        orders = {"moves": [{"from": x, "to": y, "units": 3}, {"from": x, "to": z, "units": 10}]}
        nxt, out = self.resolve({"a": self.commit("a", orders)})
        self.assertEqual(nxt["territories"][y], {"holder": "a", "units": 3})
        self.assertEqual(nxt["territories"][z], {"holder": "a", "units": 2})
        self.assertEqual(nxt["territories"][x]["units"], 0)
        self.assertEqual([e for e in out["events"] if e["kind"] == "move"],
                         [{"kind": "move", "seat": "a", "from": x, "to": y, "units": 3},
                          {"kind": "move", "seat": "a", "from": x, "to": z, "units": 2}])
        third = {"moves": [{"from": x, "to": y, "units": 5}, {"from": x, "to": z, "units": 1}]}
        self.state["powers"]["a"]["commit"] = None
        _n, out = self.resolve({"a": self.commit("a", third)})
        self.assertEqual(out["skipped"], [{"seat": "a", "order": "moves[1]", "reason": "no units left in %s" % x}])

    def test_move_from_a_territory_not_held_is_skipped(self):
        x, y, _z = self.pair()
        self.terr[x] = {"holder": "b", "units": 2}
        _n, out = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 1}]})})
        self.assertEqual(out["skipped"][0]["reason"], "%s is not held" % x)
        self.assertEqual(out["battles"], 0)

    def test_neutral_capture_costs_nothing(self):
        x, y, _z = self.pair()
        self.terr[x] = {"holder": "a", "units": 4}
        nxt, out = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 3}]})})
        self.assertEqual(nxt["territories"][y], {"holder": "a", "units": 3})
        self.assertEqual(out["events"][-1], {"kind": "capture", "territory": y, "seat": "a", "from": None, "units": 3})
        self.assertEqual(out["battles"], 0)

    def test_defender_bonus_and_winner_losses(self):
        x, y, _z = self.pair()
        self.terr[x] = {"holder": "a", "units": 5}
        self.terr[y] = {"holder": "b", "units": 3}
        # 4 attackers against 3 x 1.25 = 3.75: the attacker wins and loses floor(3.75 / 2) = 1
        nxt, out = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 4}]})})
        battle = [e for e in out["events"] if e["kind"] == "battle"][0]
        self.assertEqual(battle["forces"], {"a": 4.0, "b": 3.75})
        self.assertEqual(battle["winner"], "a")
        self.assertEqual(nxt["territories"][y], {"holder": "a", "units": 3})
        self.assertEqual(battle["destroyed"], {"b": 3})
        self.assertIsNone(battle["tie"])
        # 3 attackers against 3 defenders: 3.75 beats 3; the holder keeps y with 3 - floor(3 / 2) = 2
        self.state["powers"]["a"]["commit"] = None
        nxt, out = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 3}]})})
        battle = [e for e in out["events"] if e["kind"] == "battle"][0]
        self.assertEqual(battle["winner"], "b")
        self.assertEqual(nxt["territories"][y], {"holder": "b", "units": 2})
        self.assertEqual(nxt["territories"][x]["units"], 2)
        self.assertEqual(battle["destroyed"], {"a": 3})

    def test_winner_keeps_at_least_one_unit(self):
        x, y, _z = self.pair()
        self.terr[x] = {"holder": "a", "units": 20}
        self.terr[y] = {"holder": "b", "units": 15}
        # 19 against 18.75: wins, loses floor(18.75 / 2) = 9, keeps 10
        nxt, _o = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 19}]})})
        self.assertEqual(nxt["territories"][y], {"holder": "a", "units": 10})
        # 2 against 1 defender (1.25): wins, 2 - floor(1.25 / 2) = 2
        self.terr[x] = {"holder": "a", "units": 3}
        self.terr[y] = {"holder": "b", "units": 1}
        self.state["powers"]["a"]["commit"] = None
        nxt, _o = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 2}]})})
        self.assertEqual(nxt["territories"][y], {"holder": "a", "units": 2})
        # 3 against two others of 2 and 2 (sum 4): 3 - 2 = 1
        tid, ns = neutral_with_three_neighbours(self.match)
        self.assertIsNotNone(tid)
        for t in self.terr:
            self.terr[t] = {"holder": None, "units": 0}
        for seat, src, n in zip(SEATS, ns, (3, 2, 2)):
            self.terr[src] = {"holder": seat, "units": n + 1}
            self.state["powers"][seat]["commit"] = None
        moves = {seat: self.commit(seat, {"moves": [{"from": src, "to": tid, "units": n}]}, nonce="2" + seat.encode().hex())
                 for seat, src, n in zip(SEATS, ns, (3, 2, 2))}
        nxt, out = self.resolve(moves)
        self.assertEqual(nxt["territories"][tid], {"holder": "a", "units": 1})
        battle = [e for e in out["events"] if e["kind"] == "battle"][0]
        self.assertEqual(battle["destroyed"], {"b": 2, "c": 2})

    def test_holder_keeps_a_tie_and_rng_breaks_a_tie_between_attackers(self):
        x, y, _z = self.pair()
        self.terr[x] = {"holder": "a", "units": 6}
        self.terr[y] = {"holder": "b", "units": 4}
        # 5 against 4 x 1.25 = 5: tied, the holder keeps it
        nxt, out = self.resolve({"a": self.commit("a", {"moves": [{"from": x, "to": y, "units": 5}]})})
        battle = [e for e in out["events"] if e["kind"] == "battle"][0]
        self.assertEqual(battle["tie"], "holder")
        self.assertEqual(nxt["territories"][y], {"holder": "b", "units": max(1, 4 - 2)})
        # three equal attackers on a neutral: the dice choose, reproducibly
        tid, ns = neutral_with_three_neighbours(self.match)
        for t in self.terr:
            self.terr[t] = {"holder": None, "units": 0}
        moves = {}
        for seat, src in zip(SEATS, ns):
            self.terr[src] = {"holder": seat, "units": 3}
            self.state["powers"][seat]["commit"] = None
            moves[seat] = self.commit(seat, {"moves": [{"from": src, "to": tid, "units": 2}]}, nonce="3" + seat.encode().hex())
        winners = set()
        for text in ("one", "two", "three", "four", "five", "six"):
            n1, o1 = self.resolve(moves, rng_for(text))
            n2, o2 = self.resolve(moves, rng_for(text))
            self.assertEqual(n1, n2)
            self.assertEqual(o1, o2)
            battle = [e for e in o1["events"] if e["kind"] == "battle"][0]
            self.assertEqual(battle["tie"], "rng")
            self.assertIn(battle["winner"], ("a", "b", "c"))
            self.assertEqual(n1["territories"][tid], {"holder": battle["winner"], "units": 1})
            winners.add(battle["winner"])
        self.assertGreater(len(winners), 1)

    def test_holder_reinforcing_a_contested_territory_fights_without_the_bonus(self):
        tid, ns = neutral_with_three_neighbours(self.match)
        self.terr[tid] = {"holder": "a", "units": 2}
        self.terr[ns[0]] = {"holder": "a", "units": 3}
        self.terr[ns[1]] = {"holder": "b", "units": 5}
        moves = {"a": self.commit("a", {"moves": [{"from": ns[0], "to": tid, "units": 2}]}, "aa"),
                 "b": self.commit("b", {"moves": [{"from": ns[1], "to": tid, "units": 4}]}, "bb")}
        _n, out = self.resolve(moves)
        battle = [e for e in out["events"] if e["kind"] == "battle"][0]
        self.assertEqual(battle["forces"], {"a": 4.0, "b": 4.0})
        self.assertEqual(battle["tie"], "holder")

    def test_betrayal_only_with_an_active_pact(self):
        x, y, _z = self.pair()
        self.terr[x] = {"holder": "a", "units": 6}
        self.terr[y] = {"holder": "b", "units": 1}
        orders = {"moves": [{"from": x, "to": y, "units": 5}]}
        self.state["pacts_active"] = [["a", "b"]]
        nxt, out = self.resolve({"a": self.commit("a", orders)})
        self.assertIn({"kind": "betrayal", "seat": "a", "victim": "b", "penalty": 3}, out["events"])
        self.assertEqual(nxt["powers"]["a"]["score_penalty"], 3)
        self.assertEqual(nxt["powers"]["a"]["betrayals"], 1)
        self.state["pacts_active"] = [["a", "c"]]
        self.state["powers"]["a"]["commit"] = None
        nxt, out = self.resolve({"a": self.commit("a", orders)})
        self.assertFalse([e for e in out["events"] if e["kind"] == "betrayal"])
        self.assertEqual(nxt["powers"]["a"]["score_penalty"], 0)

    def test_pacts_need_both_sides(self):
        moves = {"a": engine_move("a", pacts=["b", "c"]), "b": engine_move("b", pacts=["a"]), "c": engine_move("c")}
        nxt, out = self.resolve(moves)
        self.assertEqual(nxt["pacts_active"], [["a", "b"]])
        self.assertEqual(out["pacts_active_next"], [["a", "b"]])
        self.assertEqual(out["pacts_active"], [])


class EconomyAndLedgerTests(unittest.TestCase):
    def setUp(self):
        self.match, self.state, self.seats = fresh(names=("ann", "bob", "cy", None))
        self.adj = matrix.adjacency(self.match["map"])
        self.yields = {tid: t["yield"] for tid, t in self.match["map"]["territories"].items()}
        self.state["round"] = 2
        self.home = {s: matrix.home_of_seat(self.match["map"], s) for s in SEATS}

    def commit(self, seat, orders, nonce="11"):
        self.state["powers"][seat]["commit"] = matrix.commit_hash(orders, nonce)
        return engine_move(seat, reveal={"orders": orders, "nonce": nonce})

    def resolve(self, moves):
        return matrix.simulate_round(self.state, self.match, self.seats, moves, rng_for())

    def test_income_is_the_yield_of_held_territories_for_joined_seats(self):
        nxt, out = self.resolve({})
        for seat in ("a", "b", "c"):
            self.assertEqual(out["income"][seat], 3)
            self.assertEqual(nxt["powers"][seat]["resources"], 8)
        self.assertNotIn("d", out["income"])
        self.assertEqual(nxt["powers"]["d"]["resources"], 5)
        neighbour = self.adj[self.home["a"]][0]
        self.state["territories"][neighbour] = {"holder": "a", "units": 1}
        nxt, out = self.resolve({})
        self.assertEqual(out["income"]["a"], 3 + self.yields[neighbour])

    def test_recruit_caps_and_cost(self):
        home = self.home["a"]
        other = self.home["b"]
        orders = {"recruit": {home: 10, other: 1}}
        nxt, out = self.resolve({"a": self.commit("a", orders)})
        self.assertEqual(nxt["territories"][home]["units"], 6 + 2)
        self.assertEqual(nxt["powers"]["a"]["resources"], 5 - 4 + 3)
        self.assertEqual(out["skipped"], [{"seat": "a", "order": "recruit[%s]" % other, "reason": "not held"}])
        self.assertIn({"kind": "recruit", "seat": "a", "territory": home, "units": 2}, out["events"])

    def test_gifts_are_capped_and_applied_in_giver_name_order(self):
        a_orders = {"give": [{"to": "bob", "amount": 9}, {"to": "nobody", "amount": 1}]}
        b_orders = {"give": [{"to": "cy", "amount": 8}]}
        moves = {"a": self.commit("a", a_orders, "aa"), "b": self.commit("b", b_orders, "bb")}
        nxt, out = self.resolve(moves)
        # ann gives first (5, all she has), then bob holds 10 and gives 8 to cy
        gives = [e for e in out["events"] if e["kind"] == "give"]
        self.assertEqual(gives, [{"kind": "give", "from": "a", "to": "b", "amount": 5},
                                 {"kind": "give", "from": "b", "to": "c", "amount": 8}])
        self.assertEqual(nxt["powers"]["a"]["resources"], 0 + 3)
        self.assertEqual(nxt["powers"]["b"]["resources"], 5 + 5 - 8 + 3)
        self.assertEqual(nxt["powers"]["c"]["resources"], 5 + 8 + 3)
        self.assertEqual(out["skipped"][0]["order"], "give[1]")

    def test_stance_ledger_attack_gift_pressure(self):
        x = self.home["a"]
        y = self.adj[x][0]
        self.state["territories"][y] = {"holder": "b", "units": 1}
        # a attacks b while saying 0.9 about b: |0.9 - 0.0| = 0.9
        a_orders = {"moves": [{"from": x, "to": y, "units": 3}], "give": [{"to": "cy", "amount": 2}]}
        moves = {"a": self.commit("a", a_orders, "aa", ), "b": engine_move("b", stance={"a": 0.5})}
        moves["a"]["stance"] = {"b": 0.9, "c": 0.4}
        nxt, out = self.resolve(moves)
        self.assertEqual(out["observed"]["a"]["b"], 0.0)
        self.assertEqual(out["observed"]["a"]["c"], 1.0)
        self.assertEqual(nxt["ledger"]["a"]["b"], {"sum": 0.9, "count": 1})
        self.assertEqual(nxt["ledger"]["a"]["c"], {"sum": 0.6, "count": 1})
        self.assertEqual(out["inconsistency"]["a"]["b"], 0.9)
        self.assertEqual(out["inconsistency"]["a"]["c"], 0.6)
        # b published a stance but revealed nothing: no observation, no ledger entry
        self.assertNotIn("b", out["observed"])
        self.assertEqual(nxt["ledger"]["b"]["a"], {"sum": 0.0, "count": 0})
        self.assertIsNone(out["inconsistency"]["b"]["a"])
        self.assertEqual(nxt["stance_history"][-1], {"round": 2, "stances": {"a": {"b": 0.9, "c": 0.4}, "b": {"a": 0.5}}})
        # pressure: moving next to c's territory without attacking c is 0.25
        tid, ns = neutral_with_three_neighbours(self.match)
        for t in self.state["territories"]:
            self.state["territories"][t] = {"holder": None, "units": 0}
        self.state["territories"][ns[0]] = {"holder": "a", "units": 4}
        self.state["territories"][ns[1]] = {"holder": "c", "units": 2}
        self.state["powers"]["a"]["commit"] = None
        moves = {"a": self.commit("a", {"moves": [{"from": ns[0], "to": tid, "units": 2}]}, "cc")}
        moves["a"]["stance"] = {"c": 1.0}
        nxt, out = self.resolve(moves)
        self.assertEqual(out["observed"]["a"], {"c": 0.25})
        self.assertEqual(nxt["ledger"]["a"]["c"], {"sum": 0.75, "count": 1})

    def test_score_formula(self):
        state = self.state
        state["territories"][self.adj[self.home["a"]][0]] = {"holder": "a", "units": 2}
        state["powers"]["a"]["resources"] = 7
        state["powers"]["a"]["score_penalty"] = 3
        scores = matrix.compute_scores(state, self.match)
        self.assertEqual(scores["a"], 2 * 3 + 7 + (6 + 2) - 3)
        self.assertEqual(scores["b"], 3 + 5 + 6)
        rows = matrix.standings(state)
        self.assertEqual(rows[0]["seat"], "a")
        self.assertEqual(rows[0]["rank"], 1)
        self.assertEqual([r["rank"] for r in rows], [1, 2, 2, 2])


class CryptoTests(unittest.TestCase):
    def test_group_constants(self):
        self.assertEqual(matrix.DH_P.bit_length(), 2048)
        self.assertEqual(matrix.DH_G, 2)
        self.assertEqual(pow(matrix.DH_G, matrix.DH_Q, matrix.DH_P), 1)

    def test_key_agreement_both_sides_derive_the_same_keys(self):
        xa, xb = matrix.secret_from_text("alice"), matrix.secret_from_text("bob")
        pa, pb = matrix.dh_public(xa), matrix.dh_public(xb)
        self.assertEqual(matrix.message_keys(xa, pb), matrix.message_keys(xb, pa))
        self.assertNotEqual(matrix.message_keys(xa, pb), matrix.message_keys(matrix.secret_from_text("eve"), pa))
        self.assertIsNotNone(matrix.parse_pubkey("%x" % pa))
        self.assertIsNone(matrix.parse_pubkey("%x" % (matrix.DH_P - 1)))
        self.assertIsNone(matrix.parse_pubkey("1"))
        self.assertIsNone(matrix.parse_pubkey("zz"))
        self.assertIsNone(matrix.parse_pubkey("%x" % (matrix.DH_P - pa)))  # a non-residue (order 2q)

    def seal(self, text, nonce, xa=None, xb=None):
        xa = xa or matrix.secret_from_text("alice")
        xb = xb or matrix.secret_from_text("bob")
        header = {"from": "alice", "to": "bob", "n": 1, "match": "m", "round": 2}
        return matrix.seal_message(xa, matrix.dh_public(xb), header, text, nonce), xa, xb

    def test_encrypt_decrypt_round_trip_and_mac_failure(self):
        msg, xa, xb = self.seal("meet at t05, bring 3 units", bytes(range(16)))
        self.assertEqual(matrix.open_message(xb, matrix.dh_public(xa), msg), "meet at t05, bring 3 units")
        self.assertEqual(matrix.open_message(xa, matrix.dh_public(xb), msg), "meet at t05, bring 3 units")
        flipped = dict(msg)
        ct = bytearray(bytes.fromhex(msg["ciphertext"]))
        ct[3] ^= 0x01
        flipped["ciphertext"] = ct.hex()
        with self.assertRaises(matrix.RefereeError):
            matrix.open_message(xb, matrix.dh_public(xa), flipped)
        altered_header = dict(msg)
        altered_header["round"] = 3
        with self.assertRaises(matrix.RefereeError):
            matrix.open_message(xb, matrix.dh_public(xa), altered_header)
        with self.assertRaises(matrix.RefereeError):
            matrix.open_message(matrix.secret_from_text("eve"), matrix.dh_public(xa), msg)

    def test_two_messages_never_share_a_keystream(self):
        text = "x" * 40
        m1, _xa, _xb = self.seal(text, bytes(16))
        m2, _xa, _xb = self.seal(text, bytes([1]) + bytes(15))
        self.assertNotEqual(m1["ciphertext"], m2["ciphertext"])
        k1 = bytes(a ^ b for a, b in zip(bytes.fromhex(m1["ciphertext"]), text.encode()))
        k2 = bytes(a ^ b for a, b in zip(bytes.fromhex(m2["ciphertext"]), text.encode()))
        self.assertNotEqual(k1, k2)
        self.assertEqual(len(matrix.keystream(b"k" * 32, bytes(16), 70)), 70)
        self.assertNotEqual(matrix.keystream(b"k" * 32, bytes(16), 64)[:32], matrix.keystream(b"k" * 32, bytes(16), 64)[32:])

    def test_the_demo_message_decrypts_with_the_derived_key_only(self):
        demo = REPO / "games" / "matrix" / "000-demo"
        path = demo / "rounds" / "002" / "messages" / "honest-a-to-honest-c-1.json"
        self.assertTrue(path.is_file(), "the demo match should hold one message in round 2")
        seed = matrix.load_match(demo)["seed"]
        with tempfile.TemporaryDirectory() as tmp:
            key_c = Path(tmp) / "c.key.json"
            matrix.write_keyfile(key_c, matrix.secret_from_text("%s demo key\n%s\nhonest-c" % (matrix.VERSION, seed)))
            self.assertEqual(matrix.decrypt_file(key_c, path), matrix.DEMO_MESSAGE)
            self.assertEqual(matrix.decrypt_file(key_c, path, demo), matrix.DEMO_MESSAGE)
            key_a = Path(tmp) / "a.key.json"
            matrix.write_keyfile(key_a, matrix.secret_from_text("%s demo key\n%s\nhonest-a" % (matrix.VERSION, seed)))
            self.assertEqual(matrix.decrypt_file(key_a, path), matrix.DEMO_MESSAGE)
            stranger = Path(tmp) / "s.key.json"
            matrix.write_keyfile(stranger, matrix.secret_from_text("someone else"))
            with self.assertRaises(matrix.RefereeError):
                matrix.decrypt_file(stranger, path)
            self.assertEqual(oct(key_c.stat().st_mode & 0o777), "0o600")
        result = matrix.read_json(demo / "rounds" / "002" / "result.json")
        self.assertEqual(result["messages"], {"honest-a-to-honest-c": 1})
        self.assertEqual(result["message_bytes"], path.stat().st_size)


class MoveFileTests(unittest.TestCase):
    def setUp(self):
        self.match, self.state, self.seats = fresh(names=("ann", "bob", None, None))
        self.home_a = matrix.home_of_seat(self.match["map"], "a")

    def check(self, obj, player="ann"):
        return matrix.check_move(obj, self.match, self.state, self.seats, player)

    def test_a_good_round_one_move(self):
        move = envelope(self.match, self.state, "ann", commit="a" * 64, stance={"bob": 0.7}, pacts=["bob"], say="hi")
        problems, m = self.check(move)
        self.assertEqual(problems, [])
        self.assertEqual(m, {"seat": "a", "commit": "a" * 64, "reveal": None, "stance": {"b": 0.7}, "pacts": ["b"], "say": "hi"})
        problems, m = self.check(envelope(self.match, self.state, "ann"))
        self.assertEqual(problems, [])
        self.assertIsNone(m["commit"])

    def test_stance_is_clamped(self):
        move = envelope(self.match, self.state, "ann", stance={"bob": 7})
        problems, m = self.check(move)
        self.assertEqual(problems, [])
        self.assertEqual(m["stance"], {"b": 1.0})
        _p, m = self.check(envelope(self.match, self.state, "ann", stance={"bob": -2}))
        self.assertEqual(m["stance"], {"b": 0.0})

    def test_bad_moves_are_reported_not_raised(self):
        base = envelope(self.match, self.state, "ann")
        bad = [
            ("not an object", []),
            ("missing fields", {"game": matrix.VERSION}),
            ("wrong game", dict(base, game="orbit/1")),
            ("wrong match", dict(base, match="other")),
            ("wrong round", dict(base, round=2)),
            ("float round", dict(base, round=1.0)),
            ("player mismatch", dict(base, player="bob")),
            ("unknown key", dict(base, extra=1)),
            ("short commit", dict(base, commit="abc")),
            ("upper hex commit", dict(base, commit="A" * 64)),
            ("reveal in round 1", dict(base, reveal={"orders": {}, "nonce": "aa"})),
            ("stance not object", dict(base, stance=[0.5])),
            ("stance unknown player", dict(base, stance={"zed": 0.5})),
            ("stance self", dict(base, stance={"ann": 0.5})),
            ("stance bool", dict(base, stance={"bob": True})),
            ("stance string", dict(base, stance={"bob": "0.5"})),
            ("pacts not list", dict(base, pacts="bob")),
            ("pacts self", dict(base, pacts=["ann"])),
            ("pacts duplicate", dict(base, pacts=["bob", "bob"])),
            ("pacts unknown", dict(base, pacts=["zed"])),
            ("pacts non-string", dict(base, pacts=[3])),
            ("say too long", dict(base, say="x" * 281)),
            ("say not string", dict(base, say=3)),
            ("too many stances", dict(base, stance={"p%d" % i: 0.5 for i in range(65)})),
        ]
        for label, obj in bad:
            problems, m = self.check(obj)
            self.assertTrue(problems, label)
            self.assertEqual(m, {}, label)
        problems, _m = self.check(dict(base, player="cy"), "cy")
        self.assertIn("'cy' has no seat in this match", problems)
        problems, _m = self.check(dict(base, player="a/b"), "a/b")
        self.assertTrue(any("player name" in p for p in problems))

    def test_bad_orders_in_a_reveal(self):
        self.state["round"] = 2
        self.state["powers"]["a"]["commit"] = "0" * 64
        base = envelope(self.match, self.state, "ann")
        adj = matrix.adjacency(self.match["map"])
        home = self.home_a
        far = [t for t in adj if t not in adj[home] and t != home][0]
        bad_orders = [
            ("list", []),
            ("unknown key", {"attack": []}),
            ("moves not list", {"moves": {}}),
            ("too many moves", {"moves": [{"from": home, "to": adj[home][0], "units": 1}] * 25}),
            ("move not object", {"moves": [1]}),
            ("move unknown key", {"moves": [{"from": home, "to": adj[home][0], "units": 1, "x": 1}]}),
            ("negative units", {"moves": [{"from": home, "to": adj[home][0], "units": -1}]}),
            ("zero units", {"moves": [{"from": home, "to": adj[home][0], "units": 0}]}),
            ("float units", {"moves": [{"from": home, "to": adj[home][0], "units": 1.5}]}),
            ("bool units", {"moves": [{"from": home, "to": adj[home][0], "units": True}]}),
            ("absurd units", {"moves": [{"from": home, "to": adj[home][0], "units": 10 ** 9}]}),
            ("unknown territory", {"moves": [{"from": home, "to": "t99", "units": 1}]}),
            ("not adjacent", {"moves": [{"from": home, "to": far, "units": 1}]}),
            ("ids not strings", {"moves": [{"from": 1, "to": 2, "units": 1}]}),
            ("recruit not object", {"recruit": []}),
            ("recruit unknown territory", {"recruit": {"t99": 1}}),
            ("recruit zero", {"recruit": {home: 0}}),
            ("too many recruits", {"recruit": {"t%02d" % i: 1 for i in range(1, 14)}}),
            ("give not list", {"give": {}}),
            ("give bad name", {"give": [{"to": "Bad/Name", "amount": 1}]}),
            ("give zero", {"give": [{"to": "bob", "amount": 0}]}),
            ("give unknown key", {"give": [{"to": "bob", "amount": 1, "why": "x"}]}),
            ("too many gives", {"give": [{"to": "bob", "amount": 1}] * 9}),
        ]
        for label, orders in bad_orders:
            problems, m = self.check(dict(base, reveal={"orders": orders, "nonce": "ab"}))
            self.assertTrue(problems, label)
            self.assertTrue(all(p.startswith("reveal") for p in problems), (label, problems))
        for label, reveal in [("not object", 3), ("no nonce", {"orders": {}}), ("bad nonce", {"orders": {}, "nonce": "XYZ"}),
                              ("empty nonce", {"orders": {}, "nonce": ""}), ("no orders", {"nonce": "ab"}),
                              ("extra key", {"orders": {}, "nonce": "ab", "x": 1})]:
            problems, _m = self.check(dict(base, reveal=reveal))
            self.assertTrue(problems, label)
        problems, m = self.check(dict(base, reveal={"orders": {"moves": [{"from": home, "to": adj[home][0], "units": 1}]}, "nonce": "ab"}))
        self.assertEqual(problems, [])
        self.assertEqual(m["reveal"]["nonce"], "ab")
        # commit in the last round, and a reveal with nothing on record
        self.state["round"] = self.match["rounds"]
        problems, _m = self.check(dict(base, round=self.state["round"], commit="0" * 64))
        self.assertTrue(any("last round" in p for p in problems))
        self.state["round"] = 3
        self.state["powers"]["a"]["commit"] = None
        problems, _m = self.check(dict(base, round=3, reveal={"orders": {}, "nonce": "ab"}))
        self.assertTrue(any("no commit on record" in p for p in problems))

    def test_parse_move_text_rejects_nan_duplicates_and_size(self):
        obj, problems = matrix.parse_move_text('{"a": NaN}')
        self.assertIsNone(obj)
        self.assertTrue(problems)
        obj, problems = matrix.parse_move_text('{"a": 1, "a": 2}')
        self.assertIsNone(obj)
        obj, problems = matrix.parse_move_text('{"a": Infinity}')
        self.assertIsNone(obj)
        obj, problems = matrix.parse_move_text("not json")
        self.assertIsNone(obj)
        obj, problems = matrix.parse_move_text('{"x": "%s"}' % ("y" * matrix.MAX_MOVE_BYTES))
        self.assertIsNone(obj)
        self.assertIn("larger", problems[0])
        obj, problems = matrix.parse_move_text('{"a": 1}')
        self.assertEqual((obj, problems), ({"a": 1}, []))

    def test_check_orders_without_a_map_checks_shape_only(self):
        problems = matrix.check_orders({"moves": [{"from": "t99", "to": "t98", "units": 1}]}, None, matrix.DEFAULT_RULES)
        self.assertEqual(problems, [])
        problems = matrix.check_orders({"moves": [{"from": "t99", "to": "t98", "units": 0}]}, None, matrix.DEFAULT_RULES)
        self.assertTrue(problems)


class BotTests(unittest.TestCase):
    def test_both_styles_write_valid_moves_through_a_lagged_round(self):
        match, state, seats = fresh(names=("ann", "bob", "cy", "dee"))
        pendings = {}
        for round_no in (1, 2, 3):
            moves = {}
            texts = []
            for seat, name in seats.items():
                style = "liar" if seat in ("b", "d") else "honest"
                move, pending, notes = matrix.bot_move(state, match, seats, name, style, pendings.get(name), "ab" * 16)
                self.assertEqual(notes, [], notes)
                problems, engine = matrix.check_move(move, match, state, seats, name)
                self.assertEqual(problems, [], problems)
                if round_no > 1:
                    self.assertIn("reveal", move)
                    self.assertEqual(matrix.commit_hash(move["reveal"]["orders"], move["reveal"]["nonce"]),
                                     state["powers"][seat]["commit"])
                if style == "liar":
                    self.assertEqual(set(move["stance"].values()), {0.9})
                    self.assertEqual(sorted(move["pacts"]), sorted(n for s, n in seats.items() if s != seat))
                else:
                    for v in move["stance"].values():
                        self.assertTrue(0.0 <= v <= 1.0)
                        self.assertEqual(round(v, 1), v)
                    self.assertEqual(len(move["pacts"]), 1)
                pendings[name] = pending
                moves[seat] = engine
                texts.append((name, matrix.canonical(move)))
            seed = matrix.round_seed(match["seed"], round_no, texts)
            state, out = matrix.simulate_round(state, match, seats, moves, random.Random(int(seed, 16)))
            if round_no > 1:
                self.assertTrue(all(r["status"] == "applied" for r in out["reveals"].values()), out["reveals"])
        self.assertTrue(any(t["holder"] is not None and match["map"]["territories"][tid]["home"] is None
                            for tid, t in state["territories"].items()))

    def test_bot_without_a_matching_sidecar_notes_the_no_reveal(self):
        match, state, seats = fresh()
        state["round"] = 2
        state["powers"]["a"]["commit"] = "0" * 64
        move, _pending, notes = matrix.bot_move(state, match, seats, "ann", "honest", None, "ab" * 16)
        self.assertNotIn("reveal", move)
        self.assertEqual(len(notes), 1)
        with self.assertRaises(matrix.RefereeError):
            matrix.bot_move(state, match, seats, "nobody", "honest")
        with self.assertRaises(matrix.RefereeError):
            matrix.bot_move(state, match, seats, "ann", "sneaky")

    def test_last_round_bot_commits_nothing(self):
        match, state, seats = fresh(order_rounds=2)
        state["round"] = 3
        move, pending, _notes = matrix.bot_move(state, match, seats, "ann", "honest")
        self.assertNotIn("commit", move)
        self.assertIsNone(pending)


class CommandTests(unittest.TestCase):
    """The CLI on a short match in a temporary directory."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dir = str(self.root / "003-test")
        self.private = str(self.root / "private")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                matrix.main([str(a) for a in args])
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
        return code, out.getvalue() + err.getvalue()

    def play(self, order_rounds=3, names=("hon-a", "liar-b", "hon-c"), upto=None, keys=False):
        code, out = self.run_cli("new", self.dir, "--seed", "s", "--rounds", order_rounds)
        self.assertEqual(code, 0, out)
        for n in names:
            args = ["join", self.dir, "--player", n]
            if keys:
                code, out = self.run_cli("keygen", "--out", self.root / ("%s.key" % n), "--from-text", "key " + n)
                self.assertEqual(code, 0, out)
                args += ["--pubkey", json.loads(out)["pubkey"]]
            code, out = self.run_cli(*args)
            self.assertEqual(code, 0, out)
        rounds = order_rounds + 1
        for rnd in range(1, (upto or rounds) + 1):
            for n in names:
                style = "liar" if n.startswith("liar") else "honest"
                code, out = self.run_cli("bot", self.dir, rnd, "--player", n, "--style", style, "--private", self.private)
                self.assertEqual(code, 0, out)
            code, out = self.run_cli("resolve", self.dir, rnd)
            self.assertEqual(code, 0, out)
        return rounds

    def test_whole_match_resolves_verifies_renders_and_scores(self):
        rounds = self.play(3)
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("4 round(s) recomputed, all match", out)
        final = matrix.read_json(Path(self.dir) / "rounds" / "004" / "result.json")
        self.assertTrue(final["final"])
        self.assertEqual(len(final["standings"]), 4)
        self.assertIn("inconsistency", final["ledger"])
        self.assertIn("stance_history", final["ledger"])
        self.assertEqual(len(final["ledger"]["stance_history"]), rounds)
        self.assertNotIn("commits", {k for k, v in final["commits"].items() if v})
        self.assertTrue((Path(self.dir) / "rounds" / "005" / "state.json").exists())
        for rnd in range(1, rounds + 1):
            code, out = self.run_cli("resolve", self.dir, "%03d" % rnd, "--check")
            self.assertEqual(code, 0, out)
        code, out = self.run_cli("score", self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("(final)", out)
        code, out = self.run_cli("ledger", self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("inconsistency", out)
        code, svg = self.run_cli("render", self.dir)
        self.assertEqual(code, 0, svg)
        root = ET.fromstring(svg)
        tags = {el.tag.split("}")[-1] for el in root.iter()}
        self.assertFalse(tags & {"script", "image", "use", "foreignObject", "a"})
        for el in root.iter():
            for attr, value in el.attrib.items():
                if attr != "xmlns":
                    self.assertNotIn("http", value)
        self.assertIn("hon-a", svg)
        self.assertIn("after round 4 (final)", svg)
        code, svg = self.run_cli("render", self.dir, "2")
        self.assertEqual(code, 0, svg)
        self.assertIn("after round 2", svg)
        committed = (Path(self.dir) / "rounds" / "002" / "result.json").read_text()
        self.assertEqual(json.dumps(json.loads(committed), sort_keys=True, indent=2, ensure_ascii=False) + "\n", committed)
        self.assertEqual(matrix.read_json(Path(self.dir) / "match.json")["rounds"], 4)
        # the bots' sidecars live in the private directory, not the match
        self.assertTrue((Path(self.private) / ".hon-a.pending.json").is_file())
        self.assertFalse(list(Path(self.dir).rglob(".*.pending.json")))

    def test_resolve_is_deterministic_and_verify_detects_tampering(self):
        self.play(2)
        first = (Path(self.dir) / "rounds" / "002" / "result.json").read_bytes()
        (Path(self.dir) / "rounds" / "002" / "result.json").unlink()
        (Path(self.dir) / "rounds" / "003" / "state.json").unlink()
        code, out = self.run_cli("resolve", self.dir, "2")
        self.assertEqual(code, 0, out)
        self.assertEqual((Path(self.dir) / "rounds" / "002" / "result.json").read_bytes(), first)
        path = Path(self.dir) / "rounds" / "002" / "result.json"
        result = json.loads(path.read_text())
        result["scores"]["a"] += 1
        path.write_text(matrix.canonical(result))
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 1)
        self.assertIn("round 002", out)
        self.assertIn("scores/a", out)
        self.assertNotEqual(matrix.compare({"x": 1.0}, {"x": 1.0 + 1e-9}), ["differs"])
        self.assertEqual(matrix.compare({"x": 1.0}, {"x": 1.0 + 1e-9}), [])
        self.assertTrue(matrix.compare({"x": 1.0}, {"x": 1.0 + 1e-6}))

    def test_never_overwrite(self):
        self.play(2, upto=1)
        code, out = self.run_cli("resolve", self.dir, "1")
        self.assertEqual(code, 1)
        self.assertIn("never overwritten", out)
        code, out = self.run_cli("new", self.dir, "--seed", "s")
        self.assertEqual(code, 1)
        self.assertIn("never recreated", out)
        code, out = self.run_cli("join", self.dir, "--player", "hon-a")
        self.assertEqual(code, 1)
        self.assertIn("never rewritten", out)
        code, out = self.run_cli("join", self.dir, "--player", "late", "--seat", "a")
        self.assertEqual(code, 1)
        self.assertIn("taken", out)
        code, out = self.run_cli("bot", self.dir, "2", "--player", "hon-a", "--private", self.private)
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("bot", self.dir, "2", "--player", "hon-a", "--private", self.private)
        self.assertEqual(code, 1)
        self.assertIn("--force", out)
        code, out = self.run_cli("keygen", "--out", self.root / "k.json")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("keygen", "--out", self.root / "k.json")
        self.assertEqual(code, 1)
        self.assertIn("never overwritten", out)

    def test_allow_absent_and_no_reveal_for_a_committed_absentee(self):
        self.play(3, upto=1)
        for n in ("hon-a", "hon-c"):
            code, out = self.run_cli("bot", self.dir, "2", "--player", n, "--private", self.private)
            self.assertEqual(code, 0, out)
        code, out = self.run_cli("resolve", self.dir, "2")
        self.assertEqual(code, 1)
        self.assertIn("liar-b", out)
        self.assertIn("--allow-absent", out)
        code, out = self.run_cli("resolve", self.dir, "2", "--allow-absent")
        self.assertEqual(code, 0, out)
        result = matrix.read_json(Path(self.dir) / "rounds" / "002" / "result.json")
        self.assertEqual(result["absent"], ["liar-b"])
        self.assertEqual(result["reveals"]["b"]["status"], "no_reveal")
        self.assertEqual(result["reputation"]["b"], 0.75)
        self.assertEqual(sorted(result["moved"]), ["hon-a", "hon-c"])
        state = matrix.read_json(Path(self.dir) / "rounds" / "003" / "state.json")
        self.assertIsNone(state["powers"]["b"]["commit"])
        self.assertIsNone(state["seats"]["d"])
        self.assertNotIn("d", result["income"])
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 0, out)

    def test_invalid_move_files_are_recorded_and_do_nothing(self):
        self.play(2, upto=1)
        moves = Path(self.dir) / "rounds" / "002" / "moves"
        moves.mkdir(parents=True, exist_ok=True)
        (moves / "hon-a.json").write_text("{not json")
        (moves / "hon-c.json").write_text(json.dumps({"game": matrix.VERSION, "match": "003-test", "round": 2,
                                                       "player": "hon-c", "stance": {"hon-a": float("nan")}}
                                                      ).replace("NaN", "NaN"))
        (moves / "liar-b.json").write_text(matrix.canonical({"game": matrix.VERSION, "match": "003-test", "round": 2,
                                                             "player": "hon-a"}))
        (moves / "Bad.Name.json").write_text("{}")
        (moves / "stranger.json").write_text(matrix.canonical({"game": matrix.VERSION, "match": "003-test", "round": 2,
                                                               "player": "stranger"}))
        for name in ("hon-a", "hon-c", "liar-b", "Bad.Name", "stranger"):
            code, out = self.run_cli("validate", self.dir, "2", moves / ("%s.json" % name))
            self.assertEqual(code, 1, name)
            self.assertIn("problem", out)
        code, out = self.run_cli("resolve", self.dir, "2")
        self.assertEqual(code, 0, out)
        result = matrix.read_json(Path(self.dir) / "rounds" / "002" / "result.json")
        self.assertEqual(sorted(result["invalid"]), ["Bad.Name", "hon-a", "hon-c", "liar-b", "stranger"])
        self.assertEqual(result["moved"], [])
        self.assertEqual(result["absent"], [])
        self.assertEqual({r["status"] for r in result["reveals"].values() if r["commit"]}, {"no_reveal"})
        self.assertEqual([e["kind"] for e in result["events"] if e["kind"] not in ("no_reveal",)], [])
        code, out = self.run_cli("verify", self.dir)
        self.assertEqual(code, 0, out)

    def test_validate_accepts_a_bot_move_and_the_move_helper_round_trip(self):
        self.play(3, upto=1)
        move_path = Path(self.dir) / "rounds" / "002" / "moves" / "hon-a.json"
        code, out = self.run_cli("bot", self.dir, "2", "--player", "hon-a", "--private", self.private, "--stdout")
        self.assertEqual(code, 0, out)
        move = json.loads(out.split("\n}\n")[0] + "\n}\n")
        self.assertEqual(move["player"], "hon-a")
        # hand-made: commit orders in round 2 through the helper, reveal them in round 3
        home = matrix.home_of_seat(matrix.load_match(self.dir)["map"], "a")
        orders = self.root / "orders.json"
        orders.write_text(json.dumps({"recruit": {home: 2}}))
        code, out = self.run_cli("commit", "--orders", orders, "--nonce", "ab" * 16, "--match", self.dir)
        self.assertEqual(code, 0, out)
        printed = json.loads(out)
        self.assertEqual(printed["commit"], matrix.commit_hash({"recruit": {home: 2}}, "ab" * 16))
        code, out = self.run_cli("move", self.dir, "2", "--player", "hon-a", "--orders", orders, "--nonce", "ab" * 16,
                                 "--stance", '{"liar-b": 0.2, "hon-c": 0.9}', "--pacts", "hon-c", "--say", "hello")
        self.assertEqual(code, 0, out)
        self.assertTrue(move_path.is_file())
        code, out = self.run_cli("validate", self.dir, "2", move_path)
        self.assertEqual(code, 0, out)
        for n in ("liar-b", "hon-c"):
            code, out = self.run_cli("bot", self.dir, "2", "--player", n, "--private", self.private)
            self.assertEqual(code, 0, out)
        code, out = self.run_cli("resolve", self.dir, "2")
        self.assertEqual(code, 0, out)
        result = matrix.read_json(Path(self.dir) / "rounds" / "002" / "result.json")
        self.assertEqual(result["says"], {"a": "hello"})
        self.assertEqual(result["stances"]["a"], {"b": 0.2, "c": 0.9})
        code, out = self.run_cli("move", self.dir, "3", "--player", "hon-a", "--prev-orders", orders, "--prev-nonce", "ab" * 16,
                                 "--stance", '{"liar-b": 0.1}')
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("move", self.dir, "3", "--player", "hon-a", "--prev-orders", orders, "--prev-nonce", "ab" * 16)
        self.assertEqual(code, 1)
        self.assertIn("--force", out)
        for n in ("liar-b", "hon-c"):
            code, out = self.run_cli("bot", self.dir, "3", "--player", n, "--private", self.private)
            self.assertEqual(code, 0, out)
        code, out = self.run_cli("resolve", self.dir, "3")
        self.assertEqual(code, 0, out)
        result = matrix.read_json(Path(self.dir) / "rounds" / "003" / "result.json")
        self.assertEqual(result["reveals"]["a"]["status"], "applied")
        self.assertIn({"kind": "recruit", "seat": "a", "territory": home, "units": 2}, result["events"])
        # a wrong nonce in the helper is caught by the referee, not the helper: the hash simply differs
        code, out = self.run_cli("move", self.dir, "4", "--player", "hon-a", "--prev-orders", orders, "--prev-nonce", "cd" * 16)
        self.assertEqual(code, 1)
        self.assertIn("no commit on record", out)

    def test_join_refuses_bad_names_and_keys(self):
        code, out = self.run_cli("new", self.dir, "--seed", "s", "--rounds", "2")
        self.assertEqual(code, 0, out)
        for bad in ("A", "../x", "a/b", "x", "toolongname" * 4, "Caps"):
            code, out = self.run_cli("join", self.dir, "--player", bad)
            self.assertEqual(code, 1, bad)
        code, out = self.run_cli("join", self.dir, "--player", "ok-1", "--pubkey", "zz")
        self.assertEqual(code, 1)
        self.assertIn("pubkey", out)
        code, out = self.run_cli("join", self.dir, "--player", "ok-1", "--pubkey", "1")
        self.assertEqual(code, 1)
        code, out = self.run_cli("join", self.dir, "--player", "ok-1", "--seat", "q")
        self.assertEqual(code, 1)
        code, out = self.run_cli("join", self.dir, "--player", "ok-1", "--seat", "3", "--session", "https://example/s")
        self.assertEqual(code, 0, out)
        record = matrix.read_json(Path(self.dir) / "players" / "ok-1.json")
        self.assertEqual((record["seat"], record["session"], record["pubkey"]), ("c", "https://example/s", None))
        self.assertFalse(list((Path(self.dir)).glob("players/*..*")))

    def test_encrypt_and_decrypt_through_the_cli(self):
        self.play(2, names=("hon-a", "hon-c"), upto=1, keys=True)
        code, out = self.run_cli("encrypt", self.dir, "2", "--key", self.root / "hon-a.key", "--from", "hon-a",
                                 "--to", "hon-c", "--message", "hold the line", "--nonce", "00" * 16)
        self.assertEqual(code, 0, out)
        path = Path(self.dir) / "rounds" / "002" / "messages" / "hon-a-to-hon-c-1.json"
        self.assertTrue(path.is_file())
        code, out = self.run_cli("encrypt", self.dir, "2", "--key", self.root / "hon-a.key", "--from", "hon-a",
                                 "--to", "hon-c", "--message", "second")
        self.assertEqual(code, 0, out)
        self.assertTrue((path.parent / "hon-a-to-hon-c-2.json").is_file())
        code, out = self.run_cli("decrypt", "--key", self.root / "hon-c.key", path)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "hold the line")
        code, out = self.run_cli("decrypt", "--key", self.root / "hon-a.key", path, "--match", self.dir)
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("keygen", "--out", self.root / "eve.key")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("decrypt", "--key", self.root / "eve.key", path)
        self.assertEqual(code, 1)
        msg = matrix.read_json(path)
        msg["ciphertext"] = ("00" if msg["ciphertext"][:2] != "00" else "01") + msg["ciphertext"][2:]
        path.write_text(matrix.canonical(msg))
        code, out = self.run_cli("decrypt", "--key", self.root / "hon-c.key", path)
        self.assertEqual(code, 1)
        self.assertIn("MAC", out)
        # the wrong sender key, a recipient without a key, and an oversized message are refused
        code, out = self.run_cli("encrypt", self.dir, "2", "--key", self.root / "hon-c.key", "--from", "hon-a",
                                 "--to", "hon-c", "--message", "x")
        self.assertEqual(code, 1)
        code, out = self.run_cli("join", self.dir, "--player", "mute")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli("encrypt", self.dir, "2", "--key", self.root / "hon-a.key", "--from", "hon-a",
                                 "--to", "mute", "--message", "x")
        self.assertEqual(code, 1)
        self.assertIn("public key", out)
        code, out = self.run_cli("encrypt", self.dir, "2", "--key", self.root / "hon-a.key", "--from", "hon-a",
                                 "--to", "hon-c", "--message", "x" * 5000)
        self.assertEqual(code, 1)
        # the referee counts the traffic and nothing else
        for n in ("hon-a", "hon-c"):
            code, out = self.run_cli("bot", self.dir, "2", "--player", n, "--private", self.private)
            self.assertEqual(code, 0, out)
        code, out = self.run_cli("resolve", self.dir, "2", "--allow-absent")
        self.assertEqual(code, 0, out)
        result = matrix.read_json(Path(self.dir) / "rounds" / "002" / "result.json")
        self.assertEqual(result["absent"], ["mute"])
        self.assertEqual(result["messages"], {"hon-a-to-hon-c": 2})
        self.assertGreater(result["message_bytes"], 0)

    def test_help_documents_every_subcommand(self):
        code, out = self.run_cli("--help")
        self.assertEqual(code, 0)
        for cmd in ("new", "join", "keygen", "commit", "move", "bot", "validate", "resolve", "verify",
                    "score", "ledger", "render", "encrypt", "decrypt", "demo"):
            self.assertIn(cmd, out)
        self.assertIn("made/matrix.md", out)

    def test_demo_command_plays_a_short_match(self):
        code, out = self.run_cli("demo", self.root / "000-demo", "--seed", "x", "--rounds", "2", "--private", self.private)
        self.assertEqual(code, 0, out)
        self.assertIn("standings:", out)
        self.assertIn("wall time", out)
        code, out = self.run_cli("verify", self.root / "000-demo")
        self.assertEqual(code, 0, out)
        self.assertIn("3 round(s)", out)
        self.assertTrue((self.root / "000-demo" / "rounds" / "002" / "messages" / "honest-a-to-honest-c-1.json").is_file())
        self.assertFalse(list((self.root / "000-demo").rglob("*.key.json")))


if __name__ == "__main__":
    unittest.main()


class DeepNesting(unittest.TestCase):
    """A move file nested deeper than the JSON decoder's recursion limit is a reported problem,
    and counts toward the round seed as its raw text; found by an input battery on 2026-10-05."""

    def test_deeply_nested_move_is_a_problem_not_a_crash(self):
        text = '{"x": ' + "[" * 5000 + "]" * 5000 + "}"
        obj, problems = matrix.parse_move_text(text)
        self.assertIsNone(obj)
        self.assertTrue(problems)
        self.assertEqual(matrix.move_text_for_seed(text), text)

