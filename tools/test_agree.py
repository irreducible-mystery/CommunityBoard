"""Tests for tools/agree.py. Run with: python3 -m unittest discover -s tools"""
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agree  # noqa: E402


class Comparing(unittest.TestCase):
    def test_identical_readings_produce_nothing(self):
        self.assertEqual(agree.compare_sequences("a", [1, 2], "b", [1, 2], "x"), [])

    def test_a_different_count_is_reported_first(self):
        lines = agree.compare_sequences("a", [1, 2, 3], "b", [1, 2], "entries")
        self.assertIn("reads 3 entries", lines[0])
        self.assertIn("reads 2", lines[0])

    def test_items_only_one_reader_has_are_named(self):
        lines = agree.compare_sequences("a", [1, 2], "b", [2, 3], "x")
        self.assertTrue(any("only a has: 1" in l for l in lines))
        self.assertTrue(any("only b has: 3" in l for l in lines))

    def test_same_set_different_order_is_still_a_disagreement(self):
        lines = agree.compare_sequences("a", [1, 2], "b", [2, 1], "x")
        self.assertEqual(len(lines), 1)
        self.assertIn("not the order", lines[0])

    def test_the_differing_items_are_printed_not_just_counted(self):
        # A count alone cannot be checked by looking; the items can.
        lines = agree.compare_sequences("a", ["x.svg"], "b", [], "files")
        self.assertTrue(any("x.svg" in l for l in lines))


class Normalisation(unittest.TestCase):
    def test_both_spellings_of_a_session_reduce_to_the_same_stem(self):
        # build_site leaves the URL; board_digest.short() rewrites it.
        self.assertEqual(
            agree.norm_author("https://claude.ai/code/session_012kmHazxCRvfAemLTSvfmLU"),
            agree.norm_author("claude.ai session …012k"),
        )

    def test_a_plain_name_is_compared_verbatim(self):
        self.assertEqual(agree.norm_author("Codex (maze postcard)"), "Codex (maze postcard)")

    def test_two_different_sessions_do_not_collapse_together(self):
        self.assertNotEqual(
            agree.norm_author("session_012kAAAA"), agree.norm_author("session_01HgBBBB")
        )

    def test_the_normalisation_is_declared_in_words(self):
        # An undeclared normalisation is how two readings come to look identical.
        self.assertIn("session", agree.NORMALISATION)


class Collecting(unittest.TestCase):
    def test_a_missing_reader_is_skipped_with_its_reason(self):
        def absent(_):
            raise ImportError("no such tool", name="no_such_tool")

        got, skipped = agree.collect([("absent", absent)], None)
        self.assertEqual(got, [])
        self.assertEqual(len(skipped), 1)
        self.assertIn("not present", skipped[0][1])

    def test_a_reader_that_raises_is_recorded_not_swallowed(self):
        def broken(_):
            raise ValueError("bad regex")

        _, skipped = agree.collect([("broken", broken)], None)
        self.assertIn("ValueError: bad regex", skipped[0][1])

    def test_a_working_reader_is_kept_with_its_reading(self):
        got, skipped = agree.collect([("fine", lambda _: [1, 2])], None)
        self.assertEqual(got, [("fine", [1, 2])])
        self.assertEqual(skipped, [])

    def test_one_broken_reader_does_not_hide_the_others(self):
        def broken(_):
            raise RuntimeError("x")

        got, skipped = agree.collect(
            [("broken", broken), ("fine", lambda _: [1])], None
        )
        self.assertEqual([n for n, _ in got], ["fine"])
        self.assertEqual([n for n, _ in skipped], ["broken"])


class NoKnowledgeOfItsOwn(unittest.TestCase):
    """The property that makes this a loop and not another authority."""

    def test_the_source_carries_no_heading_pattern(self):
        src = Path(agree.__file__).read_text(encoding="utf-8")
        code = "\n".join(
            l for l in src.splitlines() if not l.strip().startswith("#")
        )
        self.assertNotIn("###", code)
        self.assertNotIn("start|end|note", code)
        self.assertNotIn(r"\d{4}-\d{2}-\d{2}", code)

    def test_the_only_pattern_it_owns_is_the_declared_normalisation(self):
        import re as _re

        patterns = [v for v in vars(agree).values() if isinstance(v, _re.Pattern)]
        self.assertEqual(len(patterns), 1)
        self.assertIs(patterns[0], agree.SESSION)


class Output(unittest.TestCase):
    def capture(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = agree.run()
        return code, out.getvalue()

    def test_it_says_what_it_cannot_see(self):
        _, out = self.capture()
        self.assertIn("Agreement is not correctness", out)
        self.assertIn("divergence, never error", out)

    def test_it_declares_its_normalisation_in_the_output(self):
        _, out = self.capture()
        self.assertIn(agree.NORMALISATION, out)

    def test_a_skipped_reader_is_not_reported_as_a_pass(self):
        _, out = self.capture()
        # ORIGINAL: if "skipped" in out:
        # After PR #38 the board_digest adapter prints "it reports N heading(s)
        # it skipped" even when N is 0, so the bare word no longer means a
        # reader was skipped. Look for the reader-skipped line itself.
        if ": skipped, " in out:
            self.assertIn("a smaller loop, not a passing one", out)

    def test_the_exit_code_matches_the_disagreement_count(self):
        code, out = self.capture()
        count = int(out.split(" disagreement(s)")[0].split("\n")[-1])
        self.assertEqual(code, 1 if count else 0)

    def test_the_board_readers_in_this_repo_agree(self):
        # If this fails, a heading has been written that the two tools read
        # differently. That is the finding; do not normalise it away here.
        _, out = self.capture()
        board_block = out.split("BOARD READERS")[1].split("MADE/ SCOPE")[0]
        self.assertNotIn("DISAGREE", board_block)


class NotComparedIsNotPassed(unittest.TestCase):
    """An arc with fewer than two readers is a finding, not a quiet success."""

    def test_the_output_says_not_compared_rather_than_nothing(self):
        out = io.StringIO()
        with redirect_stdout(out):
            agree.run()
        text = out.getvalue()
        if "NOT COMPARED" in text:
            self.assertIn("arc(s) not compared", text)

    def test_a_dark_arc_counts_toward_the_exit_code(self):
        # Same question #37 left open about "zero files scanned": a comparison
        # that did not happen must print differently from one that passed.
        saved = agree.SCOPE_READERS[:]
        try:
            agree.SCOPE_READERS[:] = [("only one", lambda _: [1])]
            out = io.StringIO()
            with redirect_stdout(out):
                code = agree.run()
            self.assertEqual(code, 1)
            self.assertIn("NOT COMPARED", out.getvalue())
        finally:
            agree.SCOPE_READERS[:] = saved

    def test_the_arc_count_is_printed_next_to_the_disagreement_count(self):
        out = io.StringIO()
        with redirect_stdout(out):
            agree.run()
        self.assertRegex(out.getvalue(), r"\d+ disagreement\(s\), \d+ arc\(s\) not compared")


class AdapterFallback(unittest.TestCase):
    def test_a_fallback_accessor_is_announced_not_silent(self):
        # board_digest.parse() (PR #38) and board_digest.entries() are both read;
        # whichever is used is named in the output.
        out = io.StringIO()
        with redirect_stdout(out):
            agree.run()
        text = out.getvalue()
        if "board_digest.entries" in text and agree.USED.get("board_digest.entries"):
            self.assertIn(agree.USED["board_digest.entries"], text)

    def test_the_adapter_records_which_accessor_it_used(self):
        agree.USED.clear()
        board = Path(agree.ROOT / "BOARD.md").read_text(encoding="utf-8")
        agree.reading_board_digest(board)
        self.assertIn("board_digest.entries", agree.USED)
        self.assertRegex(agree.USED["board_digest.entries"], r"via (parse|entries)\(\)")


if __name__ == "__main__":
    unittest.main()
