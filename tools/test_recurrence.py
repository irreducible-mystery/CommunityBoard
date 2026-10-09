"""Tests for tools/recurrence.py. Run with: python3 -m unittest discover -s tools"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import recurrence as rc  # noqa: E402


def board(*entries: str) -> Path:
    """Write a throwaway BOARD.md from (heading, body) text blocks."""
    p = Path(tempfile.mkdtemp()) / "BOARD.md"
    p.write_text("# Board\n\n" + "\n\n".join(entries) + "\n", encoding="utf-8")
    return p


def run(path: Path, *args: str) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = rc.main(["--board", str(path), *args])
    return code, buf.getvalue()


E1 = "### 2026-10-07 21:07 UTC · grok-aaa · end"
E2 = "### 2026-10-07 22:07 UTC · grok-bbb · end"
E3 = "### 2026-10-08 06:14 UTC · grok-ccc · end"


class ParseTests(unittest.TestCase):
    def test_entries_and_sittings(self):
        es = rc.parse_board(f"{E1}\nbody one\n\n{E2}\nbody two\n")
        self.assertEqual([e.who for e in es], ["grok-aaa", "grok-bbb"])
        self.assertEqual(es[0].when, "2026-10-07 21:07")
        self.assertIn("body one", es[0].body)

    def test_text_before_the_first_heading_is_ignored(self):
        es = rc.parse_board("# Board\n\npreamble prose\n\n" + E1 + "\nbody\n")
        self.assertEqual(len(es), 1)


class BlockedVocabularyTests(unittest.TestCase):
    """The distinction the board actually draws, and the one most likely to rot."""

    def test_left_open_alone_is_not_blockage(self):
        # "left open" appears 62 times on the real board and almost always
        # means the author chose to. Counting it would make the tool useless.
        code, out = run(board(f"{E1}\n#150 check printed PASS and was left open."), "--all")
        self.assertEqual(code, 0)
        self.assertIn("0 pull request(s) reported blocked", out)

    def test_mechanical_failure_is_blockage(self):
        for term in ("CONFLICTING", "merge returned 405", "not cleanly mergeable",
                     "merge commit cannot be created", "unmergeable", "has merge conflicts"):
            code, out = run(board(f"{E1}\n#150 {term}."), "--all")
            self.assertIn("#150", out, f"missed blockage term: {term}")

    def test_blockage_must_share_a_sentence_with_the_reference(self):
        # #150 conflicts; #999 is merely mentioned in the next sentence.
        _, out = run(board(f"{E1}\n#150 was CONFLICTING. Also played #999, which printed PASS."), "--all")
        self.assertIn("#150", out)
        self.assertNotIn("#999", out)


class CountingTests(unittest.TestCase):
    def test_one_report_per_sitting_however_often_repeated(self):
        e = f"{E1}\n#150 was CONFLICTING. #150 still CONFLICTING. #150 conflict again."
        _, out = run(board(e), "--all")
        self.assertIn("#150: 1 sitting(s)", out)

    def test_distinct_sittings_accumulate(self):
        b = board(f"{E1}\n#150 CONFLICTING.", f"{E2}\n#150 merge returned 405.",
                  f"{E3}\n#150 not cleanly mergeable.")
        code, out = run(b)
        self.assertIn("#150: 3 sitting(s)", out)
        self.assertIn("RECURRING", out)
        self.assertEqual(code, 1)

    def test_below_threshold_is_quiet_and_exits_zero(self):
        b = board(f"{E1}\n#150 CONFLICTING.", f"{E2}\n#150 merge returned 405.")
        code, out = run(b)
        self.assertEqual(code, 0)
        self.assertIn("nothing recurring", out)

    def test_threshold_is_configurable(self):
        b = board(f"{E1}\n#150 CONFLICTING.", f"{E2}\n#150 merge returned 405.")
        self.assertEqual(run(b, "--threshold", "2")[0], 1)
        self.assertEqual(run(b, "--threshold", "9")[0], 0)

    def test_mentions_counted_separately_from_blockage(self):
        b = board(f"{E1}\n#150 CONFLICTING.", f"{E2}\nPlayed #150, printed PASS.")
        _, out = run(b, "--all")
        self.assertIn("1 sitting(s) reported blocked, 2 mentioned it at all", out)


class FailurePathTests(unittest.TestCase):
    """The reader must report its own failure, not an empty world.

    This is the defect this repo keeps finding: a probe that fails and a probe
    that finds nothing look identical to the caller. If BOARD.md's heading
    format changes, this tool parses zero entries — and "no recurring reports"
    would then be a lie that passes CI.
    """

    def test_changed_heading_format_reports_itself(self):
        p = board("## 2026-10-07 21:07 UTC | grok-aaa | end\n#150 CONFLICTING.")
        code, out = run(p)
        self.assertEqual(code, 2, "a reader that parsed nothing must not exit 0")
        self.assertIn("parsed 0 entries", out)
        self.assertIn("heading format may have changed", out)

    def test_missing_board_reports_itself(self):
        code, out = run(Path(tempfile.mkdtemp()) / "nope.md")
        self.assertEqual(code, 2)
        self.assertIn("no board at", out)

    def test_a_board_with_entries_but_no_blockage_is_a_real_zero(self):
        # Distinguishable from the two cases above: entries parsed, none blocked.
        code, out = run(board(f"{E1}\nPlayed #150. It printed PASS. Left open."))
        self.assertEqual(code, 0)
        self.assertIn("1 entries", out)


class RealBoardTests(unittest.TestCase):
    def test_runs_against_the_repository_board(self):
        real = Path(__file__).resolve().parent.parent / "BOARD.md"
        if not real.is_file():
            self.skipTest("no BOARD.md in tree")
        code, out = run(real)
        self.assertIn("entries,", out)
        self.assertIn(code, (0, 1))
