"""Tests for made/clearing.py. Standard library only.

    python3 -m unittest tests/test_clearing.py
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "made"))
import clearing  # noqa: E402

SEEDS = ["first-light", "room-for-chance", "quiet-hour-15", "tetralemma"] + list("abcdefghij")


def moves(f, *lines):
    return [clearing.apply(f, clearing.parse_move(t, i + 1)) for i, t in enumerate(lines)]


class Generation(unittest.TestCase):
    def test_same_seed_same_field(self):
        for s in SEEDS:
            self.assertEqual(clearing.generate(s).to_dict(), clearing.generate(s).to_dict())
        self.assertNotEqual(clearing.generate("a").render(), clearing.generate("b").render())

    def test_field_shape(self):
        for s in SEEDS:
            f = clearing.generate(s)
            self.assertEqual(f.size, clearing.SIZE)
            self.assertEqual(f.cell(*f.base), clearing.BASE)
            for i in range(f.size):
                for x, y in ((i, 0), (i, f.size - 1), (0, i), (f.size - 1, i)):
                    self.assertEqual(f.cell(x, y), clearing.BEDROCK)
            for x, y, h in f.barriers():
                self.assertIn(h, (1, 2, 3))
            self.assertEqual(f.initial_hardness, f.hardness_left())
            self.assertGreater(f.initial_hardness, 0)

    def test_playable_from_the_base(self):
        """From the base you can reach at least one fuel node and one ore node
        without breaking anything; the vault starts sealed; the ore in the field
        plus the store is at least the total hardness."""
        for s in SEEDS:
            f = clearing.generate(s)
            reach = f.reachable()
            kinds = {n.kind for p, n in f.nodes.items() if p in reach}
            self.assertEqual(kinds, {"fuel", "ore"}, s)
            self.assertFalse(f.vault_open(), s)
            ore = sum(n.amount for n in f.nodes.values() if n.kind == "ore") + f.store["ore"]
            self.assertGreaterEqual(ore, f.initial_hardness, s)

    def test_rng_is_not_pythons(self):
        r1, r2 = clearing.Rng("x"), clearing.Rng("x")
        self.assertEqual([r1.next() for _ in range(5)], [r2.next() for _ in range(5)])
        self.assertNotEqual(clearing.Rng("x").next(), clearing.Rng("y").next())


class Rules(unittest.TestCase):
    def setUp(self):
        self.f = clearing.generate("first-light")

    def test_join_and_costs(self):
        f = self.f
        out = moves(f, "ada: join")
        self.assertTrue(out[0].ok)
        r = f.rovers["ada"]
        self.assertEqual((r.x, r.y), f.base)
        self.assertEqual(r.energy, clearing.START_ENERGY)
        self.assertFalse(moves(f, "ada: join")[0].ok)              # twice
        self.assertFalse(moves(f, "bob: move n")[0].ok)            # never joined
        self.assertTrue(moves(f, "ada: wait")[0].ok)
        self.assertEqual(r.energy, clearing.START_ENERGY)          # wait is free
        self.assertTrue(moves(f, "ada: take fuel 1")[0].ok)
        self.assertEqual((r.fuel, f.store["fuel"], r.energy), (1, 1, clearing.START_ENERGY - 1))

    def test_rejected_moves_change_nothing(self):
        f = self.f
        moves(f, "ada: join")
        before = f.to_dict()
        for bad in ("ada: move up", "ada: break n", "ada: drop", "ada: refuel",
                    "ada: give nobody fuel", "ada: fly", "garbage", "ada: take ore 99"):
            out = moves(f, bad)[0]
            self.assertFalse(out.ok, bad)
            after = f.to_dict()
            before["rejected"] += 1
            self.assertEqual(before, after, bad)

    def test_unicode_digits_do_not_crash_replay(self):
        # Breaker's report (posts/2026-10-05-superninja-breaker.md): "refuel ²" passed
        # str.isdigit() and then raised in int(), which stopped replay for every reader.
        # Now a non-ASCII count is simply not a count: the move is judged like one with
        # no count, so "refuel ²" with no fuel is rejected and the record goes on.
        f = self.f
        moves(f, "ada: join")
        out = moves(f, "ada: refuel \u00b2")[0]
        self.assertFalse(out.ok)
        self.assertIn("fuel to burn", out.note)
        for odd in ("ada: take fuel \u0663", "ada: refuel \u2461", "ada: drop ore \u0661",
                    "ada: give ada fuel \u00b3"):
            moves(f, odd)                       # no exception; accepted or rejected either way
        self.assertEqual(f.accepted + f.rejected, 6)

    def test_barrier_blocks_then_breaks(self):
        """Walk to a barrier, hit it hardness times with ore, then walk through."""
        f = self.f
        moves(f, "ada: join", f"ada: take ore 2")
        # Find a barrier adjacent to a cell reachable from the base.
        reach = f.reachable()
        target = None
        for x, y, h in sorted(f.barriers()):
            for d, (dx, dy) in clearing.DIRS.items():
                if (x - dx, y - dy) in reach and h <= 2:
                    target = ((x - dx, y - dy), d, (x, y), h)
                    break
            if target:
                break
        self.assertIsNotNone(target)
        stand, d, cell, h = target
        r = f.rovers["ada"]
        # Teleport for the test; the walk is tested elsewhere.
        r.x, r.y = stand
        r.energy = 12
        self.assertFalse(moves(f, f"ada: move {d}")[0].ok)
        for i in range(h):
            out = moves(f, f"ada: break {d}")[0]
            self.assertTrue(out.ok, out.note)
        self.assertFalse(f.is_barrier(*cell))
        self.assertEqual(r.ore, 2 - h)
        self.assertTrue(moves(f, f"ada: move {d}")[0].ok)
        self.assertEqual((r.x, r.y), cell)
        self.assertEqual(f.hits, h)

    def test_dormant_and_revive(self):
        f = self.f
        moves(f, "ada: join", "bob: join")
        a, b = f.rovers["ada"], f.rovers["bob"]
        a.energy = 1
        self.assertTrue(moves(f, "ada: take ore 1")[0].ok)
        self.assertTrue(a.dormant)
        self.assertFalse(moves(f, "ada: wait")[0].ok)                  # dormant can do nothing
        self.assertFalse(moves(f, "bob: revive ada")[0].ok)            # bob has no fuel
        self.assertTrue(moves(f, "bob: take fuel 1")[0].ok)
        self.assertTrue(moves(f, "bob: revive ada")[0].ok)
        self.assertEqual(a.energy, clearing.FUEL_ENERGY)
        self.assertEqual(b.fuel, 0)
        self.assertFalse(moves(f, "bob: revive ada")[0].ok)            # not dormant any more

    def test_give_requires_adjacency(self):
        f = self.f
        moves(f, "ada: join", "bob: join", "ada: take ore 2")
        self.assertTrue(moves(f, "ada: give bob ore 1")[0].ok)
        self.assertEqual((f.rovers["ada"].ore, f.rovers["bob"].ore), (1, 1))
        f.rovers["bob"].x += 2
        self.assertFalse(moves(f, "ada: give bob ore 1")[0].ok)

    def test_capacity_and_refuel_cap(self):
        f = self.f
        moves(f, "ada: join")
        r = f.rovers["ada"]
        f.store["fuel"] = 10
        self.assertTrue(moves(f, "ada: take fuel 4")[0].ok)
        self.assertFalse(moves(f, "ada: take fuel 1")[0].ok)           # full
        r.energy = clearing.MAX_ENERGY - 1
        self.assertTrue(moves(f, "ada: refuel 2")[0].ok)
        self.assertEqual(r.energy, clearing.MAX_ENERGY)                # capped, fuel still spent
        self.assertEqual(r.fuel, 2)
        self.assertFalse(moves(f, "ada: refuel")[0].ok)                # already at max

    def test_max_rovers(self):
        f = self.f
        for i in range(clearing.MAX_ROVERS):
            self.assertTrue(moves(f, f"r{i}: join")[0].ok)
        self.assertFalse(moves(f, "late: join")[0].ok)

    def test_nothing_after_cleared(self):
        f = self.f
        moves(f, "ada: join")
        for x, y, _ in f.barriers():
            f.cells[y][x] = clearing.FLOOR
        f.cleared_at = f.accepted
        self.assertFalse(moves(f, "ada: wait")[0].ok)


class Replay(unittest.TestCase):
    def test_bots_clear_fields_and_replay_matches(self):
        """The greedy bots clear most fields with 2 or 3 rovers; replaying
        their log reproduces exactly the field they left."""
        cleared = 0
        for s in SEEDS:
            f, log, outcomes = clearing.play(s, 3)
            self.assertTrue(all(o.ok for o in outcomes), s)   # bots never make an illegal move
            g, _ = clearing.replay(s, log)
            self.assertEqual(f.to_dict(), g.to_dict(), s)
            cleared += f.cleared
        self.assertGreaterEqual(cleared, len(SEEDS) * 2 // 3, f"bots cleared only {cleared} of {len(SEEDS)}")
        self.assertTrue(clearing.play("first-light", 3)[0].cleared)

    def test_rejected_lines_are_kept_not_dropped(self):
        f, outcomes = clearing.replay("first-light", ["ada: join", "ada: fly", "", "# a comment", "ada: wait"])
        self.assertEqual([o.ok for o in outcomes], [True, False, True])
        self.assertEqual((f.accepted, f.rejected), (2, 1))

    def test_moves_from_markdown(self):
        text = (
            "### entry\n\nSome prose.\n\n```\nclearing first-light\nada: join\nada: take fuel 1\n```\n\n"
            "```\nclearing other-seed\nbob: join\n```\n\n"
            "~~~\nclearing first-light\nada: move n\n~~~\n"
            "```python\nprint('not a move block')\n```\n"
        )
        self.assertEqual(clearing.moves_from_markdown(text, "first-light"),
                         ["ada: join", "ada: take fuel 1", "ada: move n"])
        self.assertEqual(clearing.moves_from_markdown(text, "other-seed"), ["bob: join"])
        self.assertEqual(clearing.moves_from_markdown(text, "nobody"), [])

    def test_cli_runs(self):
        for argv in (["show", "first-light"], ["show", "first-light", "--json"],
                     ["play", "first-light", "--bots", "2"]):
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(clearing.main(argv), 0, argv)
            self.assertIn("first-light", out.getvalue())


if __name__ == "__main__":
    unittest.main()
