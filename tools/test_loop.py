"""Tests for tools/loop.py. Run with: python3 -m unittest discover -s tools"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import loop  # noqa: E402


class ReadingFindings(unittest.TestCase):
    def test_a_problem_line_is_counted_by_kind(self):
        self.assertEqual(
            loop.findings_of("  BOARD.md:12: problem: unparsed heading"),
            {"unparsed heading": 1},
        )

    def test_notes_are_counted_separately_from_problems(self):
        text = "x: note: out of timestamp order\ny: note: out of timestamp order"
        self.assertEqual(loop.findings_of(text), {"out of timestamp order": 2})

    def test_a_disagreement_is_one_kind(self):
        self.assertEqual(loop.findings_of("  DISAGREE  a  vs  b"), {"DISAGREE": 1})

    def test_an_uncompared_arc_is_its_own_kind(self):
        self.assertEqual(
            loop.findings_of("  NOT COMPARED: fewer than two readers"),
            {"NOT COMPARED": 1},
        )

    def test_a_clean_run_counts_nothing(self):
        self.assertEqual(loop.findings_of("16 file(s) checked, 0 problem(s).\n"), {})

    def test_a_count_line_is_not_itself_a_finding(self):
        # Totals must not register, or the board merely growing looks like change.
        self.assertEqual(loop.findings_of("0 problem(s), 14 note(s) in BOARD.md."), {})

    def test_each_line_is_counted_once(self):
        self.assertEqual(loop.findings_of("a: problem: unparsed heading"), {"unparsed heading": 1})


class TheEntryItWrites(unittest.TestCase):
    def test_the_heading_it_writes_is_well_formed(self):
        entry = loop.entry_for(0, ["check_made: exit 0; nothing"])
        heading = [l for l in entry.splitlines() if l.startswith("### ")][0]
        import re

        self.assertRegex(
            heading,
            r"^### \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC · .+ · (start|end|note)$",
        )

    def test_without_quoting_there_is_only_one_heading(self):
        entry = loop.entry_for(0, ["x"])
        self.assertEqual(len([l for l in entry.splitlines() if l.startswith("###")]), 1)

    def test_quoting_the_evidence_puts_a_second_heading_in_the_body(self):
        # This is the finding: the evidence IS an instance of what it evidences.
        entry = loop.entry_for(0, ["x"], quote_evidence=True)
        headings = [l for l in entry.splitlines() if l.startswith("###")]
        self.assertEqual(len(headings), 2)
        self.assertIn(loop.EVIDENCE, headings)

    def test_the_quoted_evidence_does_not_parse_as_a_heading(self):
        # If it parsed, quoting it would be harmless and there would be no loop.
        import re

        good = re.compile(
            r"^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\s*·\s*(.+?)\s*·\s*(start|end|note)\s*$"
        )
        self.assertIsNone(good.match(loop.EVIDENCE))
        self.assertTrue(loop.EVIDENCE.startswith("### "))


class ClassifyingTheOutcome(unittest.TestCase):
    """rest / cycle / growth, against a stub so no subprocess is needed."""

    def drive(self, states, mode="overwrite", rounds=8):
        seq = iter(states)
        real = loop.run_round
        loop.run_round = lambda work: (next(seq), ["stub"])
        try:
            return loop.iterate(mode, rounds, verbose=False)
        finally:
            loop.run_round = real

    def test_an_unchanging_state_rests(self):
        r = self.drive([("a",)] * 4)
        self.assertEqual(r["outcome"], "RESTS")
        self.assertEqual(r["period"], 1)

    def test_a_two_state_alternation_cycles_with_period_two(self):
        r = self.drive([("a",), ("b",), ("a",), ("b",)])
        self.assertEqual(r["outcome"], "CYCLES")
        self.assertEqual(r["period"], 2)

    def test_a_state_that_never_repeats_grows(self):
        r = self.drive([(f"s{i}",) for i in range(8)], rounds=6)
        self.assertEqual(r["outcome"], "GROWS")
        self.assertIsNone(r["period"])

    def test_rest_after_a_transient_is_still_rest(self):
        r = self.drive([("a",), ("b",), ("b",), ("b",)])
        self.assertEqual(r["outcome"], "RESTS")

    def test_it_never_writes_to_the_real_board(self):
        before = (loop.ROOT / "BOARD.md").read_text(encoding="utf-8")
        self.drive([("a",)] * 3, mode="accumulate")
        self.assertEqual((loop.ROOT / "BOARD.md").read_text(encoding="utf-8"), before)


class TheHeadlineExperiment(unittest.TestCase):
    """The measured result, kept as a test so a change to it is visible.

    Runs the real checkers, so it is the slow test in this file.
    """

    def test_quoting_evidence_rests_when_bounded_and_grows_when_append_only(self):
        bounded = loop.iterate("overwrite", 5, verbose=False, quote_evidence=True)
        appended = loop.iterate("accumulate", 5, verbose=False, quote_evidence=True)
        self.assertEqual(bounded["outcome"], "RESTS")
        self.assertEqual(appended["outcome"], "GROWS")

    def test_not_quoting_evidence_rests_in_both_modes(self):
        for mode in ("overwrite", "accumulate"):
            with self.subTest(mode=mode):
                r = loop.iterate(mode, 5, verbose=False, quote_evidence=False)
                self.assertEqual(r["outcome"], "RESTS")

    def test_the_live_board_has_no_self_inflicted_heading_yet(self):
        # 0 today. One pasted heading away from not being 0, which is the point.
        import check_board

        board = (loop.ROOT / "BOARD.md").read_text(encoding="utf-8")
        kinds = [f.kind for f in check_board.scan_board(board) if f.severity == check_board.PROBLEM]
        self.assertEqual(kinds, [])


if __name__ == "__main__":
    unittest.main()
