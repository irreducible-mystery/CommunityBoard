"""Tests for made/dice.py against made/dice.md. Standard library only.

    python3 -m unittest tests/test_dice.py

The anchors come from the spec, which computed them with sha256sum and no
implementation at all; the SHA-256 the tests build by hand uses hashlib
directly, not the module. The command line is run as a child process under
the same Python, which is why tools/check_code.py lists this file under
"process". Temporary files go in a temporary directory the test makes and
removes; nothing under the repository is written: importing dice must not
leave a made/__pycache__ behind either (tools/check_made.py would list it as a
file missing from the index), so bytecode writing is switched off first.
"""

import sys

sys.dont_write_bytecode = True   # before dice is imported: no made/__pycache__

import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import struct  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from contextlib import redirect_stderr, redirect_stdout  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "made"))
import dice  # noqa: E402

DICE_PY = Path(dice.__file__).resolve()
FIXTURES = Path(__file__).resolve().parent / "dice_fixtures.json"
TWO_53 = 2 ** 53
NAME = re.compile(r"^[a-z]+-[a-z]+-[1-9][0-9]?$")

# The trimming set of dice.md's "Text rules", built from the ranges it names.
SPEC_TRIM = {chr(c) for c in range(0x09, 0x0E)} | {" ", " ", " "} \
    | {chr(c) for c in range(0x2000, 0x200B)} | {" ", " ", " ", " ", "　", "﻿"}


def strict_json(value) -> str:
    """A record as text, so 1 and 1.0 (equal in Python) and key order are compared too."""
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


def by_hand(seed, stream, i):
    """Word i of a stream, from the spec's byte layout and hashlib alone."""
    def lp(text):
        data = text.encode("utf-8")
        return struct.pack(">I", len(data)) + data
    key = lp("dice/1") + lp(seed) + lp(stream) + struct.pack(">Q", i // 8)
    return struct.unpack(">8I", hashlib.sha256(key).digest())[i % 8]


def request(kind, params, seed="quiet-hour-15", stream=None):
    return {"version": "dice/1", "seed": seed, "stream": stream or kind, "kind": kind, "params": params}


def cli(*args, stdin=None):
    """Run the command line under this Python; (exit status, stdout, stderr)."""
    done = subprocess.run(
        [sys.executable, str(DICE_PY), *args], input=stdin, capture_output=True,
        text=True, encoding="utf-8", timeout=60)
    return done.returncode, done.stdout, done.stderr


class Anchors(unittest.TestCase):
    def test_words_for_seed_a_stream_b(self):
        s = dice.Dice("a").stream("b")
        self.assertEqual((s.word(0), s.word(1), s.word(2)), (3844899584, 819827472, 3336811594))
        self.assertEqual(s.word(8), 2212906652)
        self.assertEqual(s.cursor, 0)

    def test_key_bytes(self):
        key = dice.Stream("a", "b").key(0)
        self.assertEqual(len(key), 28)
        self.assertEqual(key.hex(), "00000006" "646963652f31" "00000001" "61" "00000001" "62"
                         "0000000000000000")
        self.assertEqual(hashlib.sha256(key).hexdigest(),
                         "e52c830030dd9310c6e3b44a4b7f8f784be548c04c1d368f00fb28497d304ab2")

    def test_first_uniform(self):
        self.assertEqual(dice.Dice("a").stream("b").uniform(), 8063338865194572 / TWO_53)

    def test_hashlib_by_hand_agrees_with_word(self):
        for seed, stream in (("a", "b"), ("quiet-hour-15", "field"), ("c7d70a6 claude-k7bxd8", "suggest/3"),
                             ("2026-10-05 01:46 UTC", "moves"), ("été \u2603 \U0001F300", "n")):
            s = dice.Dice(seed).stream(stream)
            for i in (0, 1, 7, 8, 9, 15, 16, 1000, 12345):
                self.assertEqual(s.word(i), by_hand(seed, stream, i), (seed, stream, i))

    def test_name_anchor(self):
        self.assertEqual(dice.Dice("336489").stream("name").name(), "quiet-hour-15")

    def test_version_and_lists(self):
        self.assertEqual(dice.VERSION, "dice/1")
        self.assertEqual(len(dice.ADJECTIVES), 64)
        self.assertEqual(len(dice.NOUNS), 64)
        self.assertEqual(len(set(dice.ADJECTIVES)), 64)
        self.assertEqual(len(set(dice.NOUNS)), 64)
        self.assertEqual(len(dice.OPERATIONS), 12)
        self.assertEqual(len(dice.CONSTRAINTS), 6)
        self.assertEqual(dice.ADJECTIVES[0], "quiet")
        self.assertEqual(dice.NOUNS[0], "hour")
        self.assertEqual(dice.OPERATIONS[2], "Change one parameter and report what moved.")
        self.assertEqual(dice.CONSTRAINTS[4], "Reproducible from a seed.")
        self.assertEqual(64 * 64 * 99, 405504)


class Draws(unittest.TestCase):
    def setUp(self):
        self.s = dice.Dice("quiet-hour-15").stream("field")

    def test_uniform_range_and_grid(self):
        for _ in range(500):
            u = self.s.uniform()
            self.assertGreaterEqual(u, 0.0)
            self.assertLess(u, 1.0)
            self.assertTrue((u * TWO_53).is_integer())
        self.assertEqual(self.s.cursor, 1000)

    def test_below_one_takes_nothing(self):
        self.assertEqual(self.s.below(1), 0)
        self.assertEqual(self.s.cursor, 0)

    def test_below_two(self):
        for _ in range(100):
            self.assertIn(self.s.below(2), (0, 1))
        self.assertEqual(self.s.cursor, 100)

    def test_below_2_32_uses_one_word(self):
        v = self.s.below(2 ** 32)
        self.assertEqual(v, self.s.word(0))
        self.assertEqual(self.s.cursor, 1)

    def test_below_2_32_plus_1_uses_two_words(self):
        n = 2 ** 32 + 1
        v = self.s.below(n)
        self.assertLess(v, n)
        self.assertEqual(self.s.cursor % 2, 0)
        self.assertGreaterEqual(self.s.cursor, 2)
        i = 0
        while True:
            w = (self.s.word(i) >> 31) * 2 ** 32 + self.s.word(i + 1)
            i += 2
            if w < n:
                break
        self.assertEqual((v, self.s.cursor), (w, i))

    def test_below_2_53_uses_two_words(self):
        v = self.s.below(TWO_53)
        self.assertEqual(v, (self.s.word(0) >> 11) * 2 ** 32 + self.s.word(1))
        self.assertEqual(self.s.cursor, 2)

    def test_below_small_bounds_by_hand(self):
        # k = 3 for n = 5: the top three bits of each word, rejected at 5, 6, 7.
        s = dice.Dice("quiet-hour-15").stream("hand")
        values = [s.below(5) for _ in range(50)]
        i = 0
        for v in values:
            while True:
                w = s.word(i) >> 29
                i += 1
                if w < 5:
                    break
            self.assertEqual(v, w)
        self.assertEqual(s.cursor, i)

    def test_between_bounds(self):
        for _ in range(300):
            self.assertIn(self.s.between(1, 6), range(1, 7))
        self.assertEqual(self.s.between(7, 7), 7)
        self.assertEqual(self.s.between(-3, -3), -3)
        for _ in range(100):
            self.assertIn(self.s.between(-5, 5), range(-5, 6))
        v = self.s.between(-(2 ** 53 - 1), 0)         # a range of 2^53, the largest allowed
        self.assertTrue(-(2 ** 53 - 1) <= v <= 0)

    def test_between_matches_below(self):
        a = dice.Dice("x").stream("y")
        b = dice.Dice("x").stream("y")
        for _ in range(50):
            self.assertEqual(a.between(10, 20), 10 + b.below(11))

    def test_choice(self):
        items = ["a", "b", "c"]
        for _ in range(100):
            self.assertIn(self.s.choice(items), items)
        self.assertEqual(self.s.choice(["only"]), "only")
        self.assertEqual(self.s.choice("q"), "q")
        with self.assertRaises(ValueError):
            self.s.choice([])

    def test_shuffle_is_a_permutation(self):
        items = list(range(40))
        got = self.s.shuffle(items)
        self.assertEqual(sorted(got), items)
        self.assertNotEqual(got, items)
        self.assertEqual(items, list(range(40)))   # the original is not touched
        self.assertIsNot(got, items)

    def test_shuffle_of_0_or_1_takes_nothing(self):
        self.assertEqual(self.s.shuffle([]), [])
        self.assertEqual(self.s.shuffle(["one"]), ["one"])
        self.assertEqual(self.s.cursor, 0)
        self.assertEqual(sorted(self.s.shuffle(("t", "u"))), ["t", "u"])
        self.assertEqual(self.s.cursor, 1)

    def test_shuffle_by_hand(self):
        s = dice.Dice("quiet-hour-15").stream("hand")
        items = list("abcdefgh")
        got = s.shuffle(items)
        copy = list(items)
        t = dice.Dice("quiet-hour-15").stream("hand")
        for i in range(len(copy) - 1, 0, -1):
            j = t.below(i + 1)
            copy[i], copy[j] = copy[j], copy[i]
        self.assertEqual(got, copy)

    def test_sample_distinct_positions(self):
        items = list(range(30))
        got = self.s.sample(items, 12)
        self.assertEqual(len(got), 12)
        self.assertEqual(len(set(got)), 12)
        self.assertTrue(all(v in items for v in got))
        self.assertEqual(items, list(range(30)))
        self.assertEqual(self.s.sample(items, 0), [])
        before = self.s.cursor
        self.assertEqual(self.s.sample([], 0), [])
        self.assertEqual(self.s.cursor, before)
        full = self.s.sample(items, 30)
        self.assertEqual(sorted(full), items)

    def test_sample_by_hand(self):
        s = dice.Dice("quiet-hour-15").stream("hand")
        got = s.sample(list(range(10)), 4)
        t = dice.Dice("quiet-hour-15").stream("hand")
        copy = list(range(10))
        for i in range(4):
            j = i + t.below(10 - i)
            copy[i], copy[j] = copy[j], copy[i]
        self.assertEqual(got, copy[:4])

    def test_weighted_never_returns_a_zero_weight_item(self):
        items = ["never", "often", "zero", "rare"]
        weights = [0, 10, 0.0, 1]
        seen = set()
        for _ in range(2000):
            got = self.s.weighted(items, weights)
            self.assertNotIn(got, ("never", "zero"))
            seen.add(got)
        self.assertEqual(seen, {"often", "rare"})
        self.assertEqual(self.s.cursor, 4000)   # two words per draw
        self.assertEqual(self.s.weighted(["only"], [3]), "only")
        self.assertEqual(self.s.weighted(["a", "b"], [0, 1]), "b")
        self.assertEqual(self.s.weighted(["a", "b"], [1, 0]), "a")

    def test_weighted_by_hand(self):
        s = dice.Dice("quiet-hour-15").stream("hand")
        t = dice.Dice("quiet-hour-15").stream("hand")
        items, weights = ["a", "b", "c"], [1, 2, 3]
        for _ in range(200):
            x = t.uniform() * 6
            want = "a" if 1 > x else ("b" if 3 > x else "c")
            self.assertEqual(s.weighted(items, weights), want)

    def test_weighted_frequency(self):
        counts = {"a": 0, "b": 0}
        for _ in range(3000):
            counts[self.s.weighted(["a", "b"], [1, 3])] += 1
        self.assertAlmostEqual(counts["b"] / 3000, 0.75, delta=0.05)

    def test_coin_frequency(self):
        for p in (0.0, 0.3, 0.5, 1.0):
            s = dice.Dice("quiet-hour-15").stream(f"coin {p}")
            heads = sum(1 for _ in range(4000) if s.coin(p))
            self.assertAlmostEqual(heads / 4000, p, delta=0.04, msg=p)
            self.assertEqual(s.cursor, 8000)
        self.assertIsInstance(self.s.coin(), bool)

    def test_coin_is_uniform_below_p(self):
        a = dice.Dice("x").stream("c")
        b = dice.Dice("x").stream("c")
        for _ in range(100):
            self.assertEqual(a.coin(0.3), b.uniform() < 0.3)

    def test_normal_mean_and_variance(self):
        n = 6000
        values = [self.s.normal() for _ in range(n)]
        mean = sum(values) / n
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        self.assertAlmostEqual(mean, 0.0, delta=0.1)
        self.assertAlmostEqual(var, 1.0, delta=0.15)
        self.assertEqual(self.s.cursor, 4 * n)

    def test_normal_by_hand(self):
        a = dice.Dice("x").stream("n")
        b = dice.Dice("x").stream("n")
        for _ in range(50):
            u, v = b.uniform(), b.uniform()
            want = math.sqrt(-2 * math.log(1 - u)) * math.cos(2 * math.pi * v)
            self.assertAlmostEqual(a.normal(), want, delta=1e-9)

    def test_hex(self):
        for n in (1, 4, 64):
            h = self.s.hex(n)
            self.assertEqual(len(h), 8 * n)
            self.assertRegex(h, r"^[0-9a-f]+$")
        s = dice.Dice("a").stream("b")
        self.assertEqual(s.hex(2), "e52c830030dd9310")

    def test_name_shape_and_lists(self):
        for _ in range(200):
            n = self.s.name()
            self.assertRegex(n, NAME)
            adjective, noun, number = n.split("-")
            self.assertIn(adjective, dice.ADJECTIVES)
            self.assertIn(noun, dice.NOUNS)
            self.assertIn(int(number), range(1, 100))

    def test_name_by_hand(self):
        a = dice.Dice("x").stream("n")
        b = dice.Dice("x").stream("n")
        for _ in range(50):
            want = f"{b.choice(dice.ADJECTIVES)}-{b.choice(dice.NOUNS)}-{b.between(1, 99)}"
            self.assertEqual(a.name(), want)

    def test_suggest(self):
        pool = ["one", "two", "three", "four", "five"]
        for _ in range(100):
            got = self.s.suggest(pool)
            self.assertEqual(list(got), ["subject", "partner", "operation", "constraint", "invitation", "choices"])
            self.assertIn(got["subject"], pool)
            self.assertIn(got["partner"], pool)
            self.assertNotEqual(got["subject"], got["partner"])
            self.assertIn(got["operation"], dice.OPERATIONS)
            self.assertIn(got["constraint"], dice.CONSTRAINTS)
            self.assertEqual(got["invitation"], got["operation"] + " Subject: " + got["subject"]
                             + ". Partner: " + got["partner"] + ". " + got["constraint"])
            self.assertEqual(got["choices"], ["accept", "reinterpret", "decline"])
        two = [self.s.suggest(["p", "q"]) for _ in range(20)]
        self.assertTrue(all({d["subject"], d["partner"]} == {"p", "q"} for d in two))

    def test_suggest_by_hand(self):
        pool = [f"item {i}" for i in range(7)]
        a = dice.Dice("x").stream("s")
        b = dice.Dice("x").stream("s")
        for _ in range(50):
            got = a.suggest(pool)
            s = b.below(7)
            t = b.below(6)
            if t >= s:
                t += 1
            op, con = b.choice(dice.OPERATIONS), b.choice(dice.CONSTRAINTS)
            self.assertEqual((got["subject"], got["partner"], got["operation"], got["constraint"]),
                             (pool[s], pool[t], op, con))

    def test_streams_independent_and_repeatable(self):
        same_a = [dice.Dice("seed").stream("one").take() for _ in range(1)]
        same_b = [dice.Dice("seed").stream("one").take() for _ in range(1)]
        self.assertEqual(same_a, same_b)
        one = dice.Dice("seed").stream("one")
        two = dice.Dice("seed").stream("two")
        self.assertNotEqual([one.take() for _ in range(8)], [two.take() for _ in range(8)])
        self.assertNotEqual(dice.Dice("seed").stream("one").take(), dice.Dice("seeds").stream("one").take())
        again = dice.Dice("seed").stream("one")
        self.assertEqual([again.take() for _ in range(8)], [dice.Dice("seed").stream("one").word(i) for i in range(8)])

    def test_word_equals_sequential_takes(self):
        taken = [self.s.take() for _ in range(40)]
        fresh = dice.Dice("quiet-hour-15").stream("field")
        self.assertEqual(taken, [fresh.word(i) for i in range(40)])
        self.assertEqual(fresh.cursor, 0)
        self.assertEqual(self.s.cursor, 40)
        self.assertEqual(self.s.word(3), taken[3])
        self.assertEqual(self.s.cursor, 40)

    def test_attributes(self):
        self.assertEqual(self.s.seed, "quiet-hour-15")
        self.assertEqual(self.s.stream, "field")
        self.assertEqual(self.s.cursor, 0)
        self.assertEqual(dice.Dice("quiet-hour-15").seed, "quiet-hour-15")

    def test_six_thousand_d6(self):
        s = dice.Dice("quiet-hour-15").stream("d6")
        faces = {f: 0 for f in range(1, 7)}
        for _ in range(6000):
            faces[s.between(1, 6)] += 1
        for face, n in faces.items():
            self.assertTrue(800 <= n <= 1200, (face, n))
        self.assertEqual(sum(faces.values()), 6000)


class Invalid(unittest.TestCase):
    def test_seeds_and_streams(self):
        with self.assertRaises(ValueError):
            dice.Dice("")
        with self.assertRaises(ValueError):
            dice.Dice("x" * 1001)
        dice.Dice("x" * 1000)
        with self.assertRaises(ValueError):
            dice.Dice("\ud800")
        with self.assertRaises(ValueError):
            dice.Dice("ok\udfff")
        with self.assertRaises(ValueError):
            dice.Dice(123)
        with self.assertRaises(ValueError):
            dice.Dice("ok").stream("")
        with self.assertRaises(ValueError):
            dice.Dice("ok").stream("y" * 1001)
        with self.assertRaises(ValueError):
            dice.Dice("ok").stream("\ud800")
        with self.assertRaises(ValueError):
            dice.Stream("ok", None)

    def test_draw_arguments(self):
        s = dice.Dice("ok").stream("s")
        for bad in (0, -1, TWO_53 + 1, 1.5, "3", True):
            with self.assertRaises(ValueError, msg=bad):
                s.below(bad)
        self.assertIn(s.below(2.0), (0, 1))          # 2.0 is accepted as the integer 2
        with self.assertRaises(ValueError):
            s.between(6, 1)
        with self.assertRaises(ValueError):
            s.between(0, 2 ** 53)                    # bound beyond the safe range
        with self.assertRaises(ValueError):
            s.between(-(2 ** 52), 2 ** 52)            # range 2^53 + 1
        s.between(-(2 ** 52), 2 ** 52 - 1)            # range 2^53
        for p in (-0.1, 1.1, 2, float("nan"), float("inf"), "0.5", None):
            with self.assertRaises(ValueError, msg=p):
                s.coin(p)
        s.coin(0)
        s.coin(1)
        for n in (0, 65, -1):
            with self.assertRaises(ValueError, msg=n):
                s.hex(n)
        with self.assertRaises(ValueError):
            s.sample([1, 2, 3], 4)
        with self.assertRaises(ValueError):
            s.sample([1, 2, 3], -1)
        with self.assertRaises(ValueError):
            s.weighted(["a", "b"], [1, -1])
        with self.assertRaises(ValueError):
            s.weighted(["a", "b"], [0, 0])
        with self.assertRaises(ValueError):
            s.weighted(["a", "b"], [1])
        with self.assertRaises(ValueError):
            s.weighted(["a"], [float("inf")])
        with self.assertRaises(ValueError):
            s.weighted([], [])
        with self.assertRaises(ValueError):
            s.suggest(["one"])
        with self.assertRaises(ValueError):
            s.suggest(["one", "one"])
        with self.assertRaises(ValueError):
            s.suggest(["one", 2])
        with self.assertRaises(ValueError):
            s.suggest([str(i) for i in range(1001)])
        with self.assertRaises(ValueError):
            s.word(-1)
        with self.assertRaises(ValueError):
            s.word(2 ** 67)

    def test_requests(self):
        ok = request("integer", {"count": 3, "min": 1, "max": 6})
        dice.run(ok)
        bad_cases = [
            dict(ok, version="dice/2"),
            dict(ok, version=1),
            dict(ok, seed=""),
            dict(ok, seed="x" * 1001),
            dict(ok, seed="\ud800"),
            dict(ok, stream=""),
            dict(ok, kind="dice"),
            dict(ok, params={"count": 0, "min": 1, "max": 6}),
            dict(ok, params={"count": 1001, "min": 1, "max": 6}),
            dict(ok, params={"count": 3, "min": 6, "max": 1}),
            dict(ok, params={"count": 3, "min": -(2 ** 52), "max": 2 ** 52}),          # range 2^53 + 1
            dict(ok, params={"count": 3, "min": 0, "max": 2 ** 53}),                   # beyond the safe range
            dict(ok, params={"count": 3, "min": 1}),                                   # max missing
            dict(ok, params={"count": 3, "min": 1, "max": 6, "extra": 1}),
            dict(ok, params=[3, 1, 6]),
            request("words", {"count": "6"}),
            request("words", {"count": 6.5}),
            request("words", {"count": True}),
            request("hex", {"words": 65}),
            request("hex", {"words": 0}),
            request("coin", {"count": 2, "p": -0.01}),
            request("coin", {"count": 2, "p": 1.01}),
            request("sample", {"pool": ["a", "b"], "k": 3}),
            request("sample", {"pool": ["a", "b"], "k": -1}),
            request("pick", {"pool": ["a", "x" * 301], "count": 1}),
            request("pick", {"pool": ["a", "   "], "count": 1}),
            request("pick", {"pool": [], "count": 1}),
            request("pick", {"pool": "ab", "count": 1}),
            request("pick", {"pool": ["a", 1], "count": 1}),
            request("pick", {"pool": [str(i) for i in range(1001)], "count": 1}),
            request("suggest", {"pool": ["a", "a "]}),
            request("suggest", {"pool": ["a"]}),
            request("weighted", {"pool": ["a", "b"], "weights": [1, -1], "count": 1}),
            request("weighted", {"pool": ["a", "b"], "weights": [0, 0], "count": 1}),
            request("weighted", {"pool": ["a", "b"], "weights": [1], "count": 1}),
            request("weighted", {"pool": ["a", "b"], "weights": [1, "1"], "count": 1}),
            request("weighted", {"pool": ["a", "b"], "weights": [1, float("nan")], "count": 1}),
        ]
        for bad in bad_cases:
            with self.assertRaises(ValueError, msg=bad):
                dice.run(bad)
        for missing in ("version", "seed", "stream", "kind", "params"):
            partial = dict(ok)
            del partial[missing]
            with self.assertRaises(ValueError, msg=missing):
                dice.run(partial)
        with self.assertRaises(ValueError):
            dice.run(dict(ok, note="extra top-level key"))
        with self.assertRaises(ValueError):
            dice.run([ok])
        # The edges that are allowed.
        dice.run(request("integer", {"count": 1000, "min": -(2 ** 52), "max": 2 ** 52 - 1}))   # range 2^53
        dice.run(request("integer", {"count": 1, "min": -(2 ** 53 - 1), "max": -(2 ** 53 - 1)}))
        dice.run(request("integer", {"count": 1, "min": 2 ** 53 - 1, "max": 2 ** 53 - 1}))
        dice.run(request("pick", {"pool": ["x" * 300], "count": 1}))
        dice.run(request("sample", {"pool": ["a", "b"], "k": 0}))
        dice.run(request("sample", {"pool": ["a", "b"], "k": 2}))
        dice.run(request("hex", {"words": 64}))
        dice.run(request("coin", {"count": 1, "p": 0}))
        dice.run(request("coin", {"count": 1, "p": 1}))
        dice.run(request("words", {"count": 1000}))
        dice.run(request("suggest", {"pool": [str(i) for i in range(1000)]}))


class Records(unittest.TestCase):
    POOL = [" alpha", "beta ", "gamma", "delta", "epsilon"]
    REQUESTS = [
        ("words", {"count": 5}),
        ("uniform", {"count": 5}),
        ("integer", {"count": 10, "min": 1, "max": 6}),
        ("normal", {"count": 4}),
        ("coin", {"count": 8, "p": 0.25}),
        ("hex", {"words": 3}),
        ("name", {"count": 6}),
        ("pick", {"pool": POOL, "count": 7}),
        ("shuffle", {"pool": POOL}),
        ("sample", {"pool": POOL, "k": 3}),
        ("weighted", {"pool": POOL, "weights": [1, 0, 2, 0.5, 3], "count": 9}),
        ("suggest", {"pool": POOL}),
    ]

    def test_every_kind_and_the_round_trip(self):
        trimmed = [p.strip() for p in self.POOL]
        for kind, params in self.REQUESTS:
            record = dice.run(request(kind, params))
            self.assertEqual(list(record), ["request", "result"])
            self.assertEqual(list(record["request"]), ["version", "seed", "stream", "kind", "params"])
            self.assertEqual(record["request"]["version"], "dice/1")
            self.assertEqual(record["request"]["kind"], kind)
            self.assertEqual(tuple(record["request"]["params"]), dice.PARAMS[kind])
            if "pool" in params:
                self.assertEqual(record["request"]["params"]["pool"], trimmed)
            # The round trip, and the record survives JSON.
            self.assertEqual(dice.run(record["request"]), record, kind)
            self.assertEqual(dice.run(json.loads(json.dumps(record))["request"]), record, kind)
            result = record["result"]
            count = params.get("count")
            if kind == "words":
                self.assertEqual(result, [dice.Dice("quiet-hour-15").stream(kind).word(i) for i in range(count)])
            elif kind == "uniform":
                self.assertTrue(all(0 <= u < 1 for u in result) and len(result) == count)
            elif kind == "integer":
                self.assertTrue(all(1 <= v <= 6 for v in result) and len(result) == count)
            elif kind == "normal":
                self.assertTrue(all(isinstance(v, float) for v in result) and len(result) == count)
            elif kind == "coin":
                self.assertTrue(all(isinstance(v, bool) for v in result) and len(result) == count)
            elif kind == "hex":
                self.assertRegex(result, r"^[0-9a-f]{24}$")
            elif kind == "name":
                self.assertTrue(all(NAME.match(v) for v in result) and len(result) == count)
            elif kind == "pick":
                self.assertTrue(all(v in trimmed for v in result) and len(result) == count)
            elif kind == "shuffle":
                self.assertEqual(sorted(result), sorted(trimmed))
            elif kind == "sample":
                self.assertEqual(len(set(result)), 3)
                self.assertTrue(all(v in trimmed for v in result))
            elif kind == "weighted":
                self.assertTrue(all(v in ("alpha", "gamma", "delta", "epsilon") for v in result))
                self.assertEqual(len(result), count)
            else:
                self.assertEqual(result["choices"], ["accept", "reinterpret", "decline"])
                self.assertNotEqual(result["subject"], result["partner"])

    def test_normalisation(self):
        record = dice.run(request("integer", {"max": 6.0, "min": 1, "count": 3.0}))
        self.assertEqual(record["request"]["params"], {"count": 3, "min": 1, "max": 6})
        self.assertIsInstance(record["request"]["params"]["count"], int)
        record = dice.run(request("sample", {"k": 1, "pool": ("  b ", "a")}))
        self.assertEqual(record["request"]["params"], {"pool": ["b", "a"], "k": 1})
        self.assertIsInstance(record["request"]["params"]["pool"], list)
        record = dice.run(request("coin", {"count": 1, "p": 1}))
        self.assertEqual(record["request"]["params"]["p"], 1)

    def test_record_matches_the_stream(self):
        record = dice.run(request("integer", {"count": 10, "min": 1, "max": 6}, seed="s", stream="t"))
        s = dice.Dice("s").stream("t")
        self.assertEqual(record["result"], [s.between(1, 6) for _ in range(10)])
        record = dice.run(request("name", {"count": 1}, seed="336489", stream="name"))
        self.assertEqual(record["result"], ["quiet-hour-15"])

    def test_checks_pass(self):
        results = dice.checks()
        self.assertGreaterEqual(len(results), 10)
        for name, ok, detail in results:
            self.assertIsInstance(name, str)
            self.assertIsInstance(detail, str)
            self.assertTrue(ok, f"{name}: {detail}")
        names = [name for name, _, _ in results]
        self.assertTrue(any("336489" in n or "quiet-hour-15" in n for n in names))

    def test_default_pool(self):
        pool = dice.default_pool()
        self.assertEqual(pool, sorted(pool))
        self.assertNotIn("README.md", pool)
        self.assertIn("dice.py", pool)
        self.assertIn("dice.md", pool)
        self.assertTrue(all(not n.startswith(".") for n in pool))
        made = DICE_PY.parent
        want = sorted(p.name for p in made.iterdir()
                      if p.is_file() and p.name != "README.md" and not p.name.startswith("."))
        self.assertEqual(pool, want)
        with tempfile.TemporaryDirectory() as d:
            for name in ("b.txt", "a.txt", ".hidden", "README.md"):
                Path(d, name).write_text("x", encoding="utf-8")
            os.mkdir(Path(d, "folder"))
            self.assertEqual(dice.default_pool(d), ["a.txt", "b.txt"])


class Fixtures(unittest.TestCase):
    """tests/dice_fixtures.json: records both implementations must reproduce."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURES, encoding="utf-8") as f:
            cls.fixtures = json.load(f)

    def test_file_shape(self):
        self.assertEqual(self.fixtures["version"], "dice/1")
        self.assertIsInstance(self.fixtures["note"], str)
        records = self.fixtures["records"]
        self.assertGreaterEqual(len(records), 1)
        for record in records:
            self.assertEqual(list(record), ["request", "result"])
            self.assertEqual(list(record["request"]), ["version", "seed", "stream", "kind", "params"])
        # Every kind is covered, so a change to any draw would show up here.
        self.assertEqual({r["request"]["kind"] for r in records}, set(dice.PARAMS))

    def test_every_record_replays(self):
        for record in self.fixtures["records"]:
            request_ = record["request"]
            got = dice.run(request_)
            with self.subTest(seed=request_["seed"], stream=request_["stream"], kind=request_["kind"]):
                # The normalised request is reproduced exactly, types and key order included.
                self.assertEqual(got["request"], request_)
                self.assertEqual(strict_json(got["request"]), strict_json(request_))
                if request_["kind"] == "normal":
                    self.assertEqual(len(got["result"]), len(record["result"]))
                    for mine, saved in zip(got["result"], record["result"]):
                        self.assertAlmostEqual(mine, saved, delta=1e-9)
                else:
                    self.assertEqual(got, record)
                    self.assertEqual(strict_json(got), strict_json(record))

    def test_a_few_records_replay_from_the_command_line_without_a_note(self):
        records = self.fixtures["records"]
        chosen = {}
        for record in records:
            chosen.setdefault(record["request"]["kind"], record)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "record.json")
            for kind in ("integer", "normal", "suggest"):
                record = chosen[kind]
                path.write_text(json.dumps(record), encoding="utf-8")
                code, out, err = cli("replay", str(path))
                self.assertEqual((code, err), (0, ""), kind)
                got = json.loads(out)
                if kind == "normal":
                    self.assertEqual(got["request"], record["request"])
                    for mine, saved in zip(got["result"], record["result"]):
                        self.assertAlmostEqual(mine, saved, delta=1e-9)
                else:
                    self.assertEqual(got, record)


class Trimming(unittest.TestCase):
    """The trimming set is named, and it is JavaScript's, not Python's."""

    def test_the_constant_is_the_spec_set(self):
        self.assertEqual(set(dice.TRIM_CHARACTERS), SPEC_TRIM)
        self.assertEqual(len(dice.TRIM_CHARACTERS), len(SPEC_TRIM))
        self.assertEqual(len(SPEC_TRIM), 25)
        # Where Python's own strip() disagrees, which is why the set is spelled out:
        # strip() keeps U+FEFF and removes U+001C; the spec does the opposite.
        self.assertEqual("﻿".strip(), "﻿")
        self.assertEqual("\x1c".strip(), "")
        self.assertEqual("﻿".strip(dice.TRIM_CHARACTERS), "")
        self.assertEqual("\x1c".strip(dice.TRIM_CHARACTERS), "\x1c")
        self.assertNotIn("\x1c", dice.TRIM_CHARACTERS)
        self.assertNotIn("\x85", dice.TRIM_CHARACTERS)

    def test_every_trim_character_is_removed_from_either_end(self):
        for ch in sorted(SPEC_TRIM):
            record = dice.run(request("pick", {"pool": [ch + ch + "abc" + ch, "d" + ch], "count": 1}))
            self.assertEqual(record["request"]["params"]["pool"], ["abc", "d"], hex(ord(ch)))
        everything = "".join(sorted(SPEC_TRIM))
        record = dice.run(request("shuffle", {"pool": [everything + "x" + everything]}))
        self.assertEqual(record["request"]["params"]["pool"], ["x"])

    def test_feff_is_trimmed(self):
        record = dice.run(request("pick", {"pool": ["﻿abc﻿"], "count": 1}))
        self.assertEqual(record["request"]["params"]["pool"], ["abc"])
        self.assertEqual(record["result"], ["abc"])
        # 300 characters plus a byte order mark on each side is still 300 after trimming.
        dice.run(request("pick", {"pool": ["﻿" + "x" * 300 + "﻿"], "count": 1}))

    def test_001c_is_not_trimmed_and_counts(self):
        record = dice.run(request("pick", {"pool": ["\x1cabc\x1c"], "count": 1}))
        self.assertEqual(record["request"]["params"]["pool"], ["\x1cabc\x1c"])
        self.assertEqual(len(record["request"]["params"]["pool"][0]), len("abc") + 2)
        self.assertEqual(record["result"], ["\x1cabc\x1c"])
        with self.assertRaises(ValueError):                    # 302 characters after trimming
            dice.run(request("pick", {"pool": ["\x1c" + "x" * 300 + "\x1c"], "count": 1}))
        # The others Python's strip() removes and the spec does not: U+001D to U+001F, U+0085.
        for ch in ("\x1d", "\x1e", "\x1f", "\x85"):
            record = dice.run(request("pick", {"pool": [ch + "abc" + ch], "count": 1}))
            self.assertEqual(record["request"]["params"]["pool"], [ch + "abc" + ch], hex(ord(ch)))
        # Only trimming is trimming: an item of nothing but U+001C is an item, not blank.
        record = dice.run(request("shuffle", {"pool": ["\x1c"]}))
        self.assertEqual(record["request"]["params"]["pool"], ["\x1c"])
        # Interior characters are never touched.
        record = dice.run(request("shuffle", {"pool": ["a ﻿ b"]}))
        self.assertEqual(record["request"]["params"]["pool"], ["a ﻿ b"])

    def test_suggest_distinctness_is_judged_after_trimming(self):
        with self.assertRaises(ValueError):
            dice.run(request("suggest", {"pool": ["a", "﻿a"]}))
        dice.run(request("suggest", {"pool": ["a", "\x1ca"]}))   # two different items

    def test_command_line_loader_trims_with_the_same_set(self):
        text = "﻿alpha\n \nbeta　\n\x1cgamma\x1c\n \t \n \ndelta one delta two\r\nepsilon\r\n"
        want = ["alpha", "beta", "\x1cgamma\x1c", "delta one delta two", "epsilon"]
        with tempfile.TemporaryDirectory() as d:
            pool = Path(d, "pool.txt")
            pool.write_bytes(text.encode("utf-8"))
            code, out, err = cli("shuffle", "quiet-hour-15", str(pool))
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out)["request"]["params"]["pool"], dice.run(
                request("shuffle", {"pool": want}))["request"]["params"]["pool"])
            self.assertEqual(sorted(json.loads(out)["request"]["params"]["pool"]), sorted(want))
        code, out, err = cli("shuffle", "quiet-hour-15", "-", stdin=text)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(sorted(json.loads(out)["request"]["params"]["pool"]), sorted(want))
        # A line of only U+00A0 is blank and dropped; a file of only such lines has no items.
        code, out, err = cli("shuffle", "quiet-hour-15", "-", stdin=" \n  \n")
        self.assertEqual((code, out), (1, ""))
        self.assertNotEqual(err, "")
        # Old Mac line endings and a file with no final newline both work.
        code, out, err = cli("shuffle", "quiet-hour-15", "-", stdin="a\rb\rc")
        self.assertEqual(sorted(json.loads(out)["request"]["params"]["pool"]), ["a", "b", "c"])


class CommandLine(unittest.TestCase):
    def test_json_output_equals_run(self):
        cases = [
            (["name", "quiet-hour-15"], request("name", {"count": 6})),
            (["integer", "quiet-hour-15", "1", "6", "10"], request("integer", {"count": 10, "min": 1, "max": 6})),
            (["integer", "quiet-hour-15", "-5", "5"], request("integer", {"count": 6, "min": -5, "max": 5})),
            (["uniform", "quiet-hour-15", "3"], request("uniform", {"count": 3})),
            (["words", "quiet-hour-15"], request("words", {"count": 6})),
            (["normal", "quiet-hour-15", "2"], request("normal", {"count": 2})),
            (["coin", "quiet-hour-15"], request("coin", {"count": 6, "p": 0.5})),
            (["coin", "quiet-hour-15", "4", "0.3"], request("coin", {"count": 4, "p": 0.3})),
            (["coin", "quiet-hour-15", "4", "1"], request("coin", {"count": 4, "p": 1})),
            (["hex", "quiet-hour-15"], request("hex", {"words": 4})),
            (["hex", "quiet-hour-15", "2"], request("hex", {"words": 2})),
        ]
        for args, req in cases:
            code, out, err = cli(*args)
            self.assertEqual((code, err), (0, ""), args)
            self.assertEqual(json.loads(out), dice.run(req), args)
            self.assertEqual(out, json.dumps(dice.run(req), indent=2, ensure_ascii=False) + "\n", args)

    def test_pools_from_files_and_stdin(self):
        text = " alpha \n\nbeta\ngamma\n   \ndelta\n"
        trimmed = ["alpha", "beta", "gamma", "delta"]
        with tempfile.TemporaryDirectory() as d:
            pool = Path(d, "pool.txt")
            pool.write_text(text, encoding="utf-8")
            code, out, err = cli("pick", "quiet-hour-15", str(pool), "3")
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out), dice.run(request("pick", {"pool": trimmed, "count": 3})))
            code, out, err = cli("shuffle", "quiet-hour-15", str(pool))
            self.assertEqual(json.loads(out), dice.run(request("shuffle", {"pool": trimmed})))
            code, out, err = cli("sample", "quiet-hour-15", "2", str(pool))
            self.assertEqual(json.loads(out), dice.run(request("sample", {"pool": trimmed, "k": 2})))
            code, out, err = cli("weighted", "quiet-hour-15", str(pool), "1,0,2.5,3", "4")
            self.assertEqual(json.loads(out), dice.run(request("weighted", {"pool": trimmed, "weights": [1, 0, 2.5, 3], "count": 4})))
            code, out, err = cli("suggest", "quiet-hour-15", str(pool))
            self.assertEqual(json.loads(out), dice.run(request("suggest", {"pool": trimmed})))
        code, out, err = cli("shuffle", "quiet-hour-15", "-", stdin=text)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), dice.run(request("shuffle", {"pool": trimmed})))
        code, out, err = cli("pick", "quiet-hour-15", "-", "2", "--plain", stdin=text)
        self.assertEqual(out.splitlines(), dice.run(request("pick", {"pool": trimmed, "count": 2}))["result"])

    def test_plain_prints_one_value_per_line(self):
        code, out, err = cli("uniform", "quiet-hour-15", "3", "--plain")
        self.assertEqual((code, err), (0, ""))
        lines = out.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual([float(x) for x in lines], dice.run(request("uniform", {"count": 3}))["result"])
        code, out, err = cli("--plain", "integer", "quiet-hour-15", "1", "6", "10")
        self.assertEqual([int(x) for x in out.splitlines()],
                         dice.run(request("integer", {"count": 10, "min": 1, "max": 6}))["result"])
        code, out, err = cli("coin", "quiet-hour-15", "4", "--plain")
        self.assertTrue(all(line in ("true", "false") for line in out.splitlines()))
        self.assertEqual(len(out.splitlines()), 4)
        code, out, err = cli("hex", "quiet-hour-15", "--plain")
        self.assertEqual(out, dice.run(request("hex", {"words": 4}))["result"] + "\n")
        code, out, err = cli("name", "336489", "1", "--plain")
        self.assertEqual(out, "quiet-hour-15\n")

    def test_stream_changes_the_stream(self):
        code, out, err = cli("uniform", "quiet-hour-15", "3", "--stream", "field")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), dice.run(request("uniform", {"count": 3}, stream="field")))
        self.assertNotEqual(json.loads(out)["result"], dice.run(request("uniform", {"count": 3}))["result"])
        code, out2, err = cli("--stream", "field", "uniform", "quiet-hour-15", "3")  # the flag may go anywhere
        self.assertEqual(out, out2)
        code, out, err = cli("suggest", "quiet-hour-15", "--stream", "suggest/1")
        self.assertEqual(json.loads(out)["request"]["stream"], "suggest/1")

    def test_bad_arguments_exit_1_with_empty_stdout(self):
        bad = [
            [],
            ["bogus", "seed"],
            ["name"],
            ["integer", "seed", "1"],
            ["integer", "seed", "6", "1"],
            ["integer", "seed", "1", "6", "x"],
            ["integer", "seed", "1", "6", "0"],
            ["integer", "seed", "1.5", "6"],
            ["uniform", "seed", "1001"],
            ["hex", "seed", "65"],
            ["coin", "seed", "3", "1.5"],
            ["coin", "seed", "3", "nan"],
            ["pick", "seed", "/no/such/file"],
            ["sample", "seed", "3", "-"],
            ["weighted", "seed", "-", "1,,2"],
            ["weighted", "seed", "-", "1"],
            ["shuffle", "seed", "-", "extra"],
            ["check", "extra"],
            ["check", "--stream", "x"],
            ["replay"],
            ["replay", "/no/such/record.json"],
            ["words", "seed", "--stream"],
            ["words", "seed", "--bogus"],
            ["words", ""],
        ]
        for args in bad:
            code, out, err = cli(*args, stdin="a\nb\n")
            self.assertEqual(code, 1, args)
            self.assertEqual(out, "", args)
            self.assertNotEqual(err, "", args)

    def test_help(self):
        code, out, err = cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("weighted  SEED POOL WEIGHTS [COUNT]", out)
        code, out, err = cli("-h")
        self.assertEqual(code, 0)

    def test_check_exits_0(self):
        code, out, err = cli("check")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("quiet-hour-15", out)
        self.assertIn("0 failed", out)
        self.assertNotIn("FAIL", out)

    def test_replay_reproduces_a_saved_record(self):
        record = dice.run(request("integer", {"count": 5, "min": 1, "max": 20}, seed="c7d70a6 example"))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "record.json")
            path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            code, out, err = cli("replay", str(path))
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out), record)
            # A bare request works too, and so does the CLI's own output.
            path.write_text(json.dumps(record["request"]), encoding="utf-8")
            code, out, err = cli("replay", str(path))
            self.assertEqual(json.loads(out), record)
            code, saved, err = cli("name", "quiet-hour-15", "3")
            path.write_text(saved, encoding="utf-8")
            code, out, err = cli("replay", str(path))
            self.assertEqual(out, saved)
            code, out, err = cli("replay", str(path), "--plain")
            self.assertEqual(out.splitlines(), json.loads(saved)["result"])
            # A record whose result was tampered with still replays, and says so.
            wrong = dict(record, result=[0, 0, 0, 0, 0])
            path.write_text(json.dumps(wrong), encoding="utf-8")
            code, out, err = cli("replay", str(path))
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out), record)
            self.assertIn("differs", err)
            path.write_text("{not json", encoding="utf-8")
            code, out, err = cli("replay", str(path))
            self.assertEqual((code, out), (1, ""))
            self.assertIn("not JSON", err)

    def test_suggest_with_no_pool_uses_default_pool(self):
        code, out, err = cli("suggest", "quiet-hour-15")
        self.assertEqual((code, err), (0, ""))
        record = json.loads(out)
        self.assertEqual(record["request"]["params"]["pool"], dice.default_pool())
        self.assertEqual(record, dice.run(request("suggest", {"pool": dice.default_pool()})))
        self.assertIn(record["result"]["subject"], dice.default_pool())

    def test_plain_suggest_is_exactly_four_lines(self):
        pool = ["one", "two", "three", "four", "five"]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "pool.txt")
            path.write_text("\n".join(pool) + "\n", encoding="utf-8")
            for extra in ((), ("--stream", "suggest/1")):
                code, out, err = cli("suggest", "quiet-hour-15", str(path), "--plain", *extra)
                self.assertEqual((code, err), (0, ""))
                stream = extra[1] if extra else None
                result = dice.run(request("suggest", {"pool": pool}, stream=stream))["result"]
                self.assertEqual(out, "".join(result[key] + "\n" for key in
                                              ("subject", "partner", "operation", "constraint")))
                lines = out.splitlines()
                self.assertEqual(len(lines), 4)
                self.assertEqual(lines, [result["subject"], result["partner"],
                                         result["operation"], result["constraint"]])
                self.assertNotIn(result["invitation"], lines)
                self.assertNotIn("accept", out)
        code, out, err = cli("suggest", "quiet-hour-15", "--plain")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(out.splitlines()), 4)
        self.assertIn(out.splitlines()[0], dice.default_pool())
        self.assertIn(out.splitlines()[2], dice.OPERATIONS)
        self.assertIn(out.splitlines()[3], dice.CONSTRAINTS)
        # Replay of a suggest record honours --plain the same way.
        code, saved, err = cli("suggest", "quiet-hour-15")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "record.json")
            path.write_text(saved, encoding="utf-8")
            code, out2, err = cli("replay", str(path), "--plain")
            self.assertEqual((code, err, out2), (0, "", out))

    def test_replay_of_a_tampered_record_notes_it_on_stderr_and_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "record.json")
            for kind, params in (("integer", {"count": 5, "min": 1, "max": 20}),
                                 ("normal", {"count": 3}),
                                 ("suggest", {"pool": ["p", "q", "r"]})):
                record = dice.run(request(kind, params, seed="c7d70a6 example"))
                if kind == "suggest":
                    wrong = dict(record, result=dict(record["result"], subject="elsewhere"))
                elif kind == "normal":
                    wrong = dict(record, result=[v + 1e-3 for v in record["result"]])
                else:
                    wrong = dict(record, result=[0 for _ in record["result"]])
                path.write_text(json.dumps(wrong), encoding="utf-8")
                code, out, err = cli("replay", str(path))
                self.assertEqual(code, 0, kind)
                self.assertEqual(json.loads(out), record, kind)      # the recomputed record is printed
                self.assertEqual(out, json.dumps(record, indent=2, ensure_ascii=False) + "\n", kind)
                self.assertIn("differs", err, kind)
                self.assertEqual(len(err.splitlines()), 1, kind)
                # --plain still prints the recomputed values, and still says so.
                code, out, err = cli("replay", str(path), "--plain")
                self.assertEqual(code, 0, kind)
                self.assertIn("differs", err, kind)
                if kind == "integer":
                    self.assertEqual([int(x) for x in out.splitlines()], record["result"])
                # The untouched record replays in silence.
                path.write_text(json.dumps(record), encoding="utf-8")
                code, out, err = cli("replay", str(path))
                self.assertEqual((code, err), (0, ""), kind)
            # replay refuses --stream: the record names its own stream.
            code, out, err = cli("replay", str(path), "--stream", "other")
            self.assertEqual((code, out), (1, ""))
            self.assertIn("stream", err)
            code, out, err = cli("--stream=other", "replay", str(path))
            self.assertEqual((code, out), (1, ""))

    def test_main_in_process(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = dice.main(["name", "336489", "1", "--plain"])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "quiet-hour-15\n", ""))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = dice.main([])
        self.assertEqual((code, out.getvalue()), (1, ""))
        self.assertIn("KIND SEED", err.getvalue())
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = dice.main(["check"])
        self.assertEqual(code, 0)


class SettledEdges(unittest.TestCase):
    """Edges settled after the cross-check of the two command lines (see dice.md)."""

    def run_cli(self, *args, stdin=None):
        import subprocess
        from pathlib import Path
        tool = Path(__file__).resolve().parents[1] / "made" / "dice.py"
        done = subprocess.run([sys.executable, str(tool), *args], input=stdin, capture_output=True, text=True)
        return done.returncode, done.stdout, done.stderr

    def test_a_seed_may_begin_with_a_dash(self):
        import json
        code, out, err = self.run_cli("name", "-x", "1")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["request"]["seed"], "-x")

    def test_unknown_and_abbreviated_options_are_refused(self):
        for args in (("name", "s", "--pl"), ("name", "s", "--str", "x"), ("name", "s", "--bogus"), ("name", "s", "--stream")):
            code, out, err = self.run_cli(*args)
            self.assertEqual((code, out), (1, ""), args)
            self.assertTrue(err, args)

    def test_numbers_on_the_command_line_are_strict_decimals(self):
        import json
        for bad in (" 0.5", "0x1", "1e999", "1_0", "inf", "nan", "", "0.5 "):
            code, out, err = self.run_cli("coin", "s", "1", bad)
            self.assertEqual((code, out), (1, ""), bad)
        for good, value in (("1e-1", 0.1), (".5", 0.5), ("1.", 1.0), ("+0.25", 0.25), ("1", 1)):
            code, out, err = self.run_cli("coin", "s", "2", good)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)["request"]["params"]["p"], value)
        code, out, err = self.run_cli("weighted", "s", "-", "1, 2", "1", stdin="a\nb\n")
        self.assertEqual((code, out), (1, ""), "a space inside WEIGHTS is not part of a decimal number")
        code, out, err = self.run_cli("weighted", "s", "-", "1,,2", "1", stdin="a\nb\nc\n")
        self.assertEqual((code, out), (1, ""), "an empty weight is missing, not zero")

    def test_integer_weights_beyond_the_safe_range_are_recorded_as_doubles(self):
        request = {"version": dice.VERSION, "seed": "wt", "stream": "w", "kind": "weighted",
                   "params": {"pool": ["a", "b", "c"], "weights": [2 ** 53 + 1, 1, 2], "count": 3}}
        recorded = dice.run(request)["request"]["params"]["weights"]
        self.assertEqual(recorded, [9007199254740992.0, 1, 2])
        self.assertIsInstance(recorded[0], float)
        self.assertIsInstance(recorded[1], int)
        huge = dict(request, params=dict(request["params"], weights=[10 ** 400, 1, 2]))
        with self.assertRaises(ValueError):
            dice.run(huge)
        with self.assertRaises(ValueError):
            dice.Dice("wt").stream("w").coin(10 ** 400)

    def test_pool_items_must_be_well_formed_text(self):
        for pool in (["\ud800"], ["ok", "a\udc00b"]):
            with self.assertRaises(ValueError):
                dice.run({"version": dice.VERSION, "seed": "s", "stream": "pick", "kind": "pick",
                          "params": {"pool": pool, "count": 1}})

    def test_pool_lines_end_at_cr_lf_or_cr_lf(self):
        import json
        code, out, err = self.run_cli("shuffle", "s", "-", stdin="a\rb\r\nc\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["request"]["params"]["pool"], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
