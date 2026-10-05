"""Tests for made/orbit.py, the Orbit referee.

Run with: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_orbit -v
"""
import json
import math
import random
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "made"))
import orbit  # noqa: E402


def quiet_rules(**changes):
    """The default world without the moon's pull, so orbits are Keplerian."""
    rules = dict(orbit.DEFAULT_RULES)
    rules["mu_moon"] = 0.0
    rules.update(changes)
    return rules


def fresh(match_id="t-match", seed="test", rounds=3, rules=None):
    match, state = orbit.new_match(match_id, seed, rounds, rules)
    return match, state


def envelope(state, player, craft):
    return {"game": orbit.VERSION, "match": state["match"], "round": state["round"],
            "player": player, "craft": craft}


class Physics(unittest.TestCase):
    def test_circular_orbit_stays_circular_without_moon(self):
        rules = quiet_rules()
        n = orbit.node_rate(2.0, rules)
        pos, vel = orbit.circular_state(2.0, 0.7, n)
        traj = orbit.propagate(pos, vel, 0.0, 1000, rules["dt"], rules, 0.0)
        self.assertEqual(len(traj), 1001)
        for x, y, _vx, _vy in traj:
            self.assertAlmostEqual(math.hypot(x, y), 2.0, delta=1e-6)
        # and it comes back to where Kepler says: angle advanced by n*T
        x, y, _vx, _vy = traj[-1]
        expected = 0.7 + n * rules["T"]
        self.assertAlmostEqual(math.atan2(y, x), math.atan2(math.sin(expected), math.cos(expected)), delta=1e-6)

    def test_energy_is_conserved_for_an_unpowered_body(self):
        rules = quiet_rules()
        pos, vel = orbit.orbit_state(3.0, 0.25, 0.4, 1.1, rules["mu"])
        traj = orbit.propagate(pos, vel, 0.0, 1000, rules["dt"], rules, 0.0)

        def energy(s):
            return 0.5 * (s[2] ** 2 + s[3] ** 2) - rules["mu"] / math.hypot(s[0], s[1])
        self.assertEqual(len(traj), 1001)
        self.assertAlmostEqual(energy(traj[0]), energy(traj[-1]), delta=1e-9)

    def test_hohmann_transfer_from_2_to_5(self):
        rules = quiet_rules()
        mu, r1, r2 = rules["mu"], 2.0, 5.0
        a = (r1 + r2) / 2
        dv1 = math.sqrt(mu * (2 / r1 - 1 / a)) - math.sqrt(mu / r1)
        dv2 = math.sqrt(mu / r2) - math.sqrt(mu * (2 / r2 - 1 / a))
        flight = math.pi * math.sqrt(a ** 3 / mu)
        dt = rules["dt"]
        k2 = int(round(flight / dt))
        pos, vel = orbit.circular_state(r1, 0.0, orbit.node_rate(r1, rules))
        # both burns prograde: along the velocity at the moment of the burn
        burns = {0: [0.0, dv1]}
        traj = orbit.propagate(pos, vel, 0.0, k2, dt, rules, 0.0, burns)
        x, y, vx, vy = traj[-1]
        speed = math.hypot(vx, vy)
        burns[k2] = [dv2 * vx / speed, dv2 * vy / speed]
        traj = orbit.propagate(pos, vel, 0.0, k2 + 500, dt, rules, 0.0, burns)
        self.assertEqual(len(traj), k2 + 501)
        for x, y, vx, vy in traj[k2:]:
            self.assertAlmostEqual(math.hypot(x, y), r2, delta=rules["capture_radius"])
            self.assertAlmostEqual(math.hypot(vx, vy), math.sqrt(mu / r2), delta=rules["capture_speed"])

    def test_step_index_matches_multiples_of_dt(self):
        for k in range(0, 1000, 7):
            self.assertEqual(orbit.step_index(orbit.burn_time(k, 0.02), 0.02), k)
        self.assertEqual(orbit.step_index(3.4, 0.02), 170)
        self.assertEqual(orbit.step_index(0.0, 0.02), 0)
        self.assertEqual(orbit.step_index(19.999, 0.02), 999)


class Rounds(unittest.TestCase):
    """simulate_round driven directly, no files."""

    def setUp(self):
        self.match, self.state = fresh(rules=quiet_rules())
        self.rules = self.match["rules"]
        self.seats = {"a": "alice", "b": "bob", "c": None, "d": None}

    def run_round(self, plans, state=None):
        return orbit.simulate_round(state or self.state, self.rules, self.seats, plans, random.Random(7))

    def test_burn_reduces_fuel_and_changes_velocity(self):
        plans = {"alice": {"a1": {"burns": [(0.0, [0.0, 0.1]), (5.0, [0.05, 0.0])], "fire": None}}, "bob": {}}
        nxt, out = self.run_round(plans)
        self.assertAlmostEqual(nxt["craft"]["a1"]["fuel"], 2.0 - 0.15, places=9)
        self.assertEqual(nxt["craft"]["a2"]["fuel"], 2.0)
        burns = [e for e in out["events"] if e["kind"] == "burn"]
        self.assertEqual([(e["id"], e["t"]) for e in burns], [("a1", 0.0), ("a1", 5.0)])

    def test_over_budget_burns_are_rejected(self):
        state = orbit._copy(self.state)
        state["craft"]["a1"]["fuel"] = 0.1
        ok = envelope(state, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0, 0.09]}]}})
        self.assertEqual(orbit.check_move(ok, self.match, state, self.seats, "alice")[0], [])
        big = envelope(state, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0, 0.11]}]}})
        problems, plan = orbit.check_move(big, self.match, state, self.seats, "alice")
        self.assertTrue(any("fuel" in p for p in problems))
        self.assertEqual(plan, {})
        split = envelope(state, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0, 0.06]}, {"t": 1.0, "dv": [0.06, 0.0]}]}})
        problems, _ = orbit.check_move(split, self.match, state, self.seats, "alice")
        self.assertTrue(any("total" in p for p in problems))
        many = envelope(state, "alice", {"a1": {"burns": [{"t": float(i), "dv": [0.0, 0.001]} for i in range(5)]}})
        problems, _ = orbit.check_move(many, self.match, state, self.seats, "alice")
        self.assertTrue(any("at most 4" in p for p in problems))

    def test_slug_hits_a_co_orbiting_target(self):
        state = orbit._copy(self.state)
        n = orbit.node_rate(2.0, self.rules)
        state["craft"]["a1"]["pos"], state["craft"]["a1"]["vel"] = orbit.circular_state(2.0, 0.0, n)
        state["craft"]["b1"]["pos"], state["craft"]["b1"]["vel"] = orbit.circular_state(2.0, 0.05, n)
        for cid in ("a2", "a3", "b2", "b3"):
            state["craft"][cid]["alive"] = False
        state["debris"] = {}
        ax, ay = state["craft"]["a1"]["pos"]
        bx, by = state["craft"]["b1"]["pos"]
        d = math.hypot(bx - ax, by - ay)
        dv = [0.3 * (bx - ax) / d, 0.3 * (by - ay) / d]
        plans = {"alice": {"a1": {"burns": [], "fire": (0.0, dv)}}, "bob": {}}
        rules = dict(self.rules)
        rules["debris_per_round"] = 0
        nxt, out = orbit.simulate_round(state, rules, self.seats, plans, random.Random(1))
        hits = [e for e in out["events"] if e["kind"] == "hit"]
        self.assertEqual(len(hits), 1)
        self.assertEqual((hits[0]["id"], hits[0]["by"], hits[0]["shooter"], hits[0]["points"]), ("b1", "s1", "alice", 3))
        self.assertFalse(nxt["craft"]["b1"]["alive"])
        self.assertTrue(nxt["craft"]["a1"]["alive"])
        self.assertEqual(nxt["craft"]["a1"]["slugs"], 1)
        self.assertEqual(out["scores_delta"]["alice"], 3)
        self.assertEqual(nxt["kills"]["alice"], 1)
        self.assertEqual(list(nxt["debris"]), [hits[0]["debris"]])   # the wreck, and the slug was consumed
        self.assertEqual(nxt["slugs"], {})

    def test_unseated_craft_give_no_points_and_leftover_slugs_become_debris(self):
        state = orbit._copy(self.state)
        n = orbit.node_rate(2.0, self.rules)
        state["craft"]["a1"]["pos"], state["craft"]["a1"]["vel"] = orbit.circular_state(2.0, 0.0, n)
        state["craft"]["c1"]["pos"], state["craft"]["c1"]["vel"] = orbit.circular_state(2.0, 0.05, n)
        state["debris"] = {}
        ax, ay = state["craft"]["a1"]["pos"]
        cx, cy = state["craft"]["c1"]["pos"]
        d = math.hypot(cx - ax, cy - ay)
        plans = {"alice": {"a1": {"burns": [], "fire": (0.0, [0.3 * (cx - ax) / d, 0.3 * (cy - ay) / d])},
                           "a2": {"burns": [], "fire": (1.0, [0.0, 0.3])}}, "bob": {}}
        nxt, out = self.run_round(plans, state)
        hits = [e for e in out["events"] if e["kind"] == "hit"]
        self.assertEqual([(h["id"], h["points"]) for h in hits], [("c1", 0)])
        self.assertEqual(out["scores_delta"]["alice"], 0)
        spawned = [e for e in out["events"] if e["kind"] == "debris_spawn" and e.get("source") == "slug"]
        self.assertEqual(len(spawned), 1)
        self.assertEqual(nxt["slugs"], {})
        self.assertEqual(len(nxt["debris"]), 3)   # the round's piece, the wreck, the stray slug

    def park(self, state, cid, nid, offset):
        """Put a craft beside a node, co-moving, offset along the orbit."""
        npos, nvel = orbit.node_state(state["nodes"][nid], state["t"], self.rules)
        speed = math.hypot(*nvel)
        state["craft"][cid]["pos"] = [npos[0] + offset * nvel[0] / speed, npos[1] + offset * nvel[1] / speed]
        state["craft"][cid]["vel"] = list(nvel)

    def test_capture_goes_to_the_closest_and_persists(self):
        state = orbit._copy(self.state)
        state["debris"] = {}
        self.park(state, "a1", "n1", 0.06)
        self.park(state, "b1", "n1", 0.02)
        self.park(state, "c1", "n2", 0.01)           # unseated: never captures
        self.park(state, "a2", "n3", 0.01)
        state["craft"]["a2"]["vel"][0] += 0.2        # too fast relative to the station
        nxt, out = self.run_round({"alice": {}, "bob": {}}, state)
        captures = {e["node"]: e["player"] for e in out["events"] if e["kind"] == "capture"}
        self.assertEqual(captures, {"n1": "bob"})
        self.assertEqual(nxt["nodes"]["n1"]["owner"], "bob")
        self.assertIsNone(nxt["nodes"]["n2"]["owner"])
        self.assertIsNone(nxt["nodes"]["n3"]["owner"])
        self.assertEqual(out["scores_delta"], {"alice": 0, "bob": 1})
        # the owner keeps the node after leaving it, when nobody else qualifies
        state2 = orbit._copy(nxt)
        state2["craft"]["b1"]["alive"] = False
        state2["craft"]["a1"]["alive"] = False
        nxt2, out2 = self.run_round({"alice": {}, "bob": {}}, state2)
        self.assertEqual(nxt2["nodes"]["n1"]["owner"], "bob")
        self.assertEqual(out2["scores_delta"]["bob"], 1)
        self.assertEqual(nxt2["scores"]["bob"], 2)

    def test_reentry_and_escape(self):
        state = orbit._copy(self.state)
        state["craft"]["a1"]["vel"] = [0.0, 0.0]                 # falls straight in
        state["craft"]["b1"]["pos"] = [21.0, 0.0]
        state["craft"]["b1"]["vel"] = [1.0, 0.0]                 # well above escape speed, outward
        nxt, out = self.run_round({"alice": {}, "bob": {}}, state)
        kinds = {e["id"]: e["kind"] for e in out["events"] if e["kind"] in ("reentry", "escaped")}
        self.assertEqual(kinds, {"a1": "reentry", "b1": "escaped"})
        self.assertFalse(nxt["craft"]["a1"]["alive"])
        self.assertFalse(nxt["craft"]["b1"]["alive"])
        self.assertTrue(all(len(out["traces"][c]) < 21 for c in ("a1", "b1")))

    def test_moon_impact(self):
        rules = dict(orbit.DEFAULT_RULES)
        match, state = fresh(rules=rules)
        mx, my = orbit.moon_position(state["moon"]["phase"], 0.0, rules)
        state["craft"]["a1"]["pos"] = [mx * 0.98, my * 0.98]
        state["craft"]["a1"]["vel"] = [0.0, 0.0]
        nxt, out = orbit.simulate_round(state, rules, self.seats, {"alice": {}, "bob": {}}, random.Random(3))
        self.assertIn(("a1", "moon_impact"), [(e["id"], e["kind"]) for e in out["events"]])

    def test_round_output_is_deterministic_and_compact(self):
        plans = {"alice": {"a1": {"burns": [(0.0, [0.1, 0.0])], "fire": (2.0, [0.2, 0.1])}}, "bob": {}}
        a = orbit.canonical(orbit.rounded(self.run_round(plans)))
        b = orbit.canonical(orbit.rounded(self.run_round(plans)))
        self.assertEqual(a, b)
        self.assertLess(len(a), 200 * 1024)
        self.assertNotIn("NaN", a)


class MoveFiles(unittest.TestCase):
    def setUp(self):
        self.match, self.state = fresh()
        self.seats = {"a": "alice", "b": "bob", "c": None, "d": None}

    def check(self, obj, player="alice"):
        return orbit.check_move(obj, self.match, self.state, self.seats, player)[0]

    def test_envelope_and_structure(self):
        self.assertEqual(self.check(envelope(self.state, "alice", {})), [])
        self.assertTrue(self.check({"craft": {}}))
        self.assertTrue(self.check(envelope(self.state, "alice", {}) | {"round": 2}))
        self.assertTrue(self.check(envelope(self.state, "alice", {}) | {"match": "other"}))
        self.assertTrue(self.check(envelope(self.state, "alice", {}) | {"game": "orbit/2"}))
        self.assertTrue(self.check(envelope(self.state, "bob", {}), "alice"))      # player != file name
        self.assertTrue(self.check(envelope(self.state, "carol", {}), "carol"))    # no seat
        self.assertTrue(self.check(envelope(self.state, "alice", {}) | {"note": "hi"}))
        self.assertTrue(self.check(envelope(self.state, "alice", {"b1": {}})))     # not my seat
        self.assertTrue(self.check(envelope(self.state, "alice", {"zz": {}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"warp": 1}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"burns": [{"t": 25.0, "dv": [0.0, 0.1]}]}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"burns": [{"t": -1.0, "dv": [0.0, 0.1]}]}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"burns": [{"t": True, "dv": [0.0, 0.1]}]}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0]}]}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"fire": {"t": 0.0, "dv": [0.4, 0.0]}}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a1": {"fire": [0.0, 0.1]}})))
        self.assertTrue(self.check(envelope(self.state, "alice", {"a" + str(i): {} for i in range(100)})))
        self.assertEqual(self.check(envelope(self.state, "alice", {"a1": {"burns": [], "fire": None}})), [])
        dead = orbit._copy(self.state)
        dead["craft"]["a1"]["alive"] = False
        self.assertTrue(orbit.check_move(envelope(dead, "alice", {"a1": {}}), self.match, dead, self.seats, "alice")[0])
        empty = orbit._copy(self.state)
        empty["craft"]["a1"]["slugs"] = 0
        self.assertTrue(orbit.check_move(envelope(empty, "alice", {"a1": {"fire": {"t": 0.0, "dv": [0.1, 0.0]}}}),
                                         self.match, empty, self.seats, "alice")[0])

    def test_text_level_rejections(self):
        for text in ('{"craft": {}', '{"a": NaN}', '{"a": Infinity}', '{"a": 1, "a": 2}', "[]", "42", "",
                     "x" * (orbit.MAX_MOVE_BYTES + 1)):
            obj, problems = orbit.parse_move_text(text)
            if obj is not None:
                problems = self.check(obj)
            self.assertTrue(problems, text[:30])

    def test_names(self):
        for bad in ("A", "a", "x" * 33, "../x", "a/b", "name_with_underscore", "", "sp ace"):
            self.assertIsNone(orbit.NAME_RE.match(bad), bad)
        for good in ("ab", "claude-hg2t", "0" * 32):
            self.assertIsNotNone(orbit.NAME_RE.match(good), good)


class Matches(unittest.TestCase):
    """The file layer, in a temporary directory."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "003-mini"
        orbit.create_match(self.dir, "mini", 3)
        orbit.join_match(self.dir, "alice", "a", "https://example.test/alice")
        orbit.join_match(self.dir, "bob", None, None)
        self.match = orbit.load_match(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def write_move(self, round_no, player, craft, override=None):
        state = orbit.load_state(self.dir, round_no)
        move = envelope(state, player, craft) | (override or {})
        path = orbit.round_dir(self.dir, round_no) / "moves" / f"{player}.json"
        orbit.write_json(path, move)
        return path

    def test_new_and_join_refusals(self):
        with self.assertRaises(orbit.RefereeError):
            orbit.create_match(self.dir, "again", 3)
        with self.assertRaises(orbit.RefereeError):
            orbit.join_match(self.dir, "alice", "c", None)          # file exists
        with self.assertRaises(orbit.RefereeError):
            orbit.join_match(self.dir, "carol", "a", None)          # seat taken
        with self.assertRaises(orbit.RefereeError):
            orbit.join_match(self.dir, "Carol", None, None)         # bad name
        with self.assertRaises(orbit.RefereeError):
            orbit.join_match(self.dir, "../x", None, None)
        seats, players, problems = orbit.load_seats(self.dir)
        self.assertEqual(seats, {"a": "alice", "b": "bob", "c": None, "d": None})
        self.assertEqual(players["alice"]["joined_round"], 1)
        self.assertEqual(problems, [])
        self.assertFalse((self.dir / "players" / ".." / "x.json").exists())
        empty = Path(self.tmp.name) / "004-empty"
        orbit.create_match(empty, "nobody", 2)
        with self.assertRaises(orbit.RefereeError):
            orbit.resolve_round(empty, 1, allow_absent=True)     # nobody has joined
        self.assertFalse((orbit.round_dir(empty, 1) / "result.json").exists())

    def test_three_rounds_resolve_verify_and_finish(self):
        for n in (1, 2, 3):
            state = orbit.load_state(self.dir, n)
            seats, _p, _q = orbit.load_seats(self.dir)
            move, _notes = orbit.bot_move(state, self.match, seats, "alice", "greedy" if n < 3 else "hawk")
            self.assertEqual(orbit.check_move(move, self.match, state, seats, "alice")[0], [])
            orbit.write_json(orbit.round_dir(self.dir, n) / "moves" / "alice.json", move)
            self.write_move(n, "bob", {"b1": {"burns": [{"t": 0.0, "dv": [0.0, 0.05]}]}})
            result, nxt, diffs = orbit.resolve_round(self.dir, n)
            self.assertEqual(diffs, [])
            self.assertEqual(result["moved"], ["alice", "bob"])
            self.assertEqual(result["absent"], [])
            self.assertEqual(result["invalid"], {})
            self.assertEqual(result["seats"], {"a": "alice", "b": "bob", "c": None, "d": None})
            self.assertEqual(nxt["round"], n + 1)
            self.assertEqual(len(result["seed"]), 64)
            self.assertEqual(result["next_state_sha256"],
                             orbit.sha256_text((orbit.round_dir(self.dir, n + 1) / "state.json").read_text(encoding="utf-8")))
            self.assertEqual("final" in result, n == 3)
        final = orbit.read_json(orbit.round_dir(self.dir, 3) / "result.json")
        self.assertTrue(final["final"])
        self.assertEqual([r["player"] for r in final["standings"]][:0], [])
        self.assertEqual({r["player"] for r in final["standings"]}, {"alice", "bob"})
        self.assertEqual(final["standings"][0]["rank"], 1)
        checked, diffs = orbit.verify_match(self.dir)
        self.assertEqual((checked, diffs), (3, []))
        # bob's fuel went down by exactly the three burns
        last = orbit.load_state(self.dir, 4)
        self.assertAlmostEqual(last["craft"]["b1"]["fuel"], 2.0 - 0.15, places=8)
        with self.assertRaises(orbit.RefereeError):
            orbit.resolve_round(self.dir, 1)                        # never overwrite
        with self.assertRaises(orbit.RefereeError):
            orbit.join_match(self.dir, "carol", None, None)         # finished
        # tampering is detected by verify
        path = orbit.round_dir(self.dir, 2) / "result.json"
        tampered = orbit.read_json(path)
        tampered["scores"]["bob"] += 1
        orbit.write_json(path, tampered)
        checked, diffs = orbit.verify_match(self.dir)
        self.assertEqual(checked, 3)
        self.assertTrue(any("scores/bob" in d for d in diffs))
        # the drawing of the last round is plain SVG
        svg = orbit.render_svg(self.match, orbit.load_state(self.dir, 3), final)
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertNotIn("<script", svg)
        self.assertNotIn("http", svg.replace("http://www.w3.org/2000/svg", ""))

    def test_resolve_is_byte_identical_across_runs(self):
        self.write_move(1, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0, 0.1]}], "fire": {"t": 1.0, "dv": [0.1, 0.2]}}})
        self.write_move(1, "bob", {})
        orbit.resolve_round(self.dir, 1)
        first = (orbit.round_dir(self.dir, 1) / "result.json").read_bytes()
        state2 = (orbit.round_dir(self.dir, 2) / "state.json").read_bytes()
        (orbit.round_dir(self.dir, 1) / "result.json").unlink()
        (orbit.round_dir(self.dir, 2) / "state.json").unlink()
        orbit.resolve_round(self.dir, 1)
        self.assertEqual((orbit.round_dir(self.dir, 1) / "result.json").read_bytes(), first)
        self.assertEqual((orbit.round_dir(self.dir, 2) / "state.json").read_bytes(), state2)

    def test_invalid_moves_are_recorded_and_ignored(self):
        self.write_move(1, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0, 0.1]}]}}, {"player": "bob"})  # wrong player
        path = orbit.round_dir(self.dir, 1) / "moves" / "bob.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"game": "orbit/1", "match": "003-mini", "round": 1, "player": "bob", '
                        '"craft": {"b1": {"burns": [{"t": 0.0, "dv": [NaN, 0.1]}]}}}\n', encoding="utf-8")
        (path.parent / "carol.json").write_text("not json at all", encoding="utf-8")
        result, nxt, _ = orbit.resolve_round(self.dir, 1)
        self.assertEqual(result["moved"], [])
        self.assertEqual(result["absent"], [])
        self.assertEqual(sorted(result["invalid"]), ["alice", "bob", "carol"])
        self.assertTrue(any("player" in p for p in result["invalid"]["alice"]))
        self.assertTrue(any("NaN" in p for p in result["invalid"]["bob"]))
        self.assertEqual(nxt["craft"]["a1"]["fuel"], 2.0)
        self.assertEqual(nxt["craft"]["b1"]["fuel"], 2.0)
        self.assertEqual([e for e in result["events"] if e["kind"] == "burn"], [])

    def test_too_many_burns_is_invalid(self):
        self.write_move(1, "alice", {"a1": {"burns": [{"t": float(i), "dv": [0.0, 0.01]} for i in range(5)]}})
        self.write_move(1, "bob", {})
        result, _n, _d = orbit.resolve_round(self.dir, 1)
        self.assertIn("alice", result["invalid"])
        self.assertEqual(result["moved"], ["bob"])

    def test_absent_players(self):
        self.write_move(1, "alice", {})
        with self.assertRaises(orbit.RefereeError):
            orbit.resolve_round(self.dir, 1)
        result, _n, _d = orbit.resolve_round(self.dir, 1, allow_absent=True)
        self.assertEqual(result["absent"], ["bob"])
        self.assertEqual(result["moved"], ["alice"])
        checked, diffs = orbit.verify_match(self.dir)
        self.assertEqual((checked, diffs), (1, []))

    def test_seed_changes_with_any_move(self):
        self.write_move(1, "alice", {})
        self.write_move(1, "bob", {})
        state = orbit.load_state(self.dir, 1)
        seats, _p, _q = orbit.load_seats(self.dir)
        texts = orbit.read_moves(self.dir, 1, self.match, state, seats)[3]
        seed1 = orbit.round_seed("mini", 1, texts)
        self.write_move(1, "bob", {"b1": {"burns": [{"t": 0.0, "dv": [0.0, 0.001]}]}})
        texts2 = orbit.read_moves(self.dir, 1, self.match, state, seats)[3]
        self.assertNotEqual(seed1, orbit.round_seed("mini", 1, texts2))
        self.assertNotEqual(seed1, orbit.round_seed("mini", 2, texts))
        self.assertNotEqual(seed1, orbit.round_seed("other", 1, texts))
        self.assertEqual(seed1, orbit.round_seed("mini", 1, list(reversed(texts))))   # order is by name

    def test_cli_validate_and_bot(self):
        path = self.write_move(1, "alice", {"a1": {"burns": [{"t": 0.0, "dv": [0.0, 0.1]}]}})
        orbit.main(["validate", str(self.dir), "1", str(path)])
        bad = self.write_move(1, "bob", {"a1": {}})
        with self.assertRaises(SystemExit) as caught:
            orbit.main(["validate", str(self.dir), "001", str(bad)])
        self.assertEqual(caught.exception.code, 1)
        bad.unlink()
        orbit.main(["bot", str(self.dir), "1", "--player", "bob", "--style", "hawk"])
        self.assertTrue((orbit.round_dir(self.dir, 1) / "moves" / "bob.json").is_file())
        with self.assertRaises(SystemExit):
            orbit.main(["bot", str(self.dir), "1", "--player", "bob"])      # exists, no --force
        orbit.main(["resolve", str(self.dir), "1"])
        with self.assertRaises(SystemExit):
            orbit.main(["resolve", str(self.dir), "1"])
        orbit.main(["resolve", str(self.dir), "1", "--check"])
        orbit.main(["verify", str(self.dir)])
        orbit.main(["score", str(self.dir)])


if __name__ == "__main__":
    unittest.main()
