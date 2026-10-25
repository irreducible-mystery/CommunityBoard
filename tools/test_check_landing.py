"""Tests for check_landing.py: the pure part only. Nothing here runs git or gh."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_landing as cl  # noqa: E402


BOARD = "# Board\n\n### 2026-10-01 00:00 UTC · a · note\n\nx\n\n### 2026-10-02 00:00 UTC · b · note\n\ny\n"


class CountTests(unittest.TestCase):
    def test_counts_headings_only(self):
        self.assertEqual(cl.count_entries(BOARD), 2)

    def test_placeholder_is_zero(self):
        self.assertEqual(cl.count_entries("WILL_REPLACE\n"), 0)
        self.assertEqual(cl.count_entries("$(cat /tmp/BOARD_full.md)\n"), 0)

    def test_heading_inside_a_line_does_not_count(self):
        self.assertEqual(cl.count_entries("text ### not a heading\n"), 0)


class GapTests(unittest.TestCase):
    def test_no_gap_when_main_is_whole(self):
        prs = [{"number": 1, "entries": 400}, {"number": 2, "entries": 10}]
        self.assertEqual(cl.gaps(442, prs), [])

    def test_gap_when_a_pr_holds_more(self):
        # The shape of 2026-10-18: main at 19, #208 at 394, #223 at 442.
        prs = [{"number": 208, "entries": 394}, {"number": 223, "entries": 442}, {"number": 5, "entries": 0}]
        found = cl.gaps(19, prs)
        self.assertEqual([p["number"] for p in found], [223, 208])
        self.assertEqual(found[0]["gap"], 423)

    def test_equal_is_not_a_gap(self):
        self.assertEqual(cl.gaps(19, [{"number": 1, "entries": 19}]), [])


class ReportTests(unittest.TestCase):
    def test_clean_report_names_the_count(self):
        self.assertIn("holds 442 entries", cl.report(442, [], 40))

    def test_failing_report_names_the_pr_and_the_command(self):
        found = cl.gaps(19, [{"number": 223, "entries": 442, "head": "abc1234", "age_days": 1,
                              "main_commits_since": 26}])
        text = cl.report(19, found, 40)
        self.assertIn("#223: 442 entries (+423)", text)
        self.assertIn("open 1 day(s)", text)
        self.assertIn("26 commit(s) to BOARD.md", text)
        self.assertIn("git diff --stat origin/main abc1234 -- BOARD.md", text)
        self.assertIn("has not landed", text)


if __name__ == "__main__":
    unittest.main()
