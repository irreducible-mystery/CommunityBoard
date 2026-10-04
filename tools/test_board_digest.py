"""Tests for tools/board_digest.py. Run with: python3 -m unittest discover -s tools

Each test here covers something the digest used to pass over without saying
anything: a heading that did not parse, a timestamp running backwards, a missing
posts/ directory, two sessions whose ids share a prefix, and two different days
counted as a filename collision.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import board_digest as bd  # noqa: E402


def run(board_text: str) -> str:
    rows, skipped = bd.parse(board_text)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bd.report_entries(rows, skipped, "BOARD.md")
    return buf.getvalue()


def entry(when: str, author: str, kind: str = "note") -> str:
    return f"### {when} UTC · {author} · {kind}\n\nBody.\n\n"


class GapTests(unittest.TestCase):
    def test_forward_gap(self):
        self.assertEqual(bd.gap_label(9), "+9m")
        self.assertEqual(bd.gap_label(0), "+0m")

    def test_backwards_gap_is_signed_once(self):
        # Was rendered "+-9m" by f"+{minutes}m".
        self.assertEqual(bd.gap_label(-9), "-9m")
        self.assertEqual(bd.gap_label(-11), "-11m")


class OrderTests(unittest.TestCase):
    def test_out_of_order_entry_is_named(self):
        text = (entry("2026-10-04 03:30", "A")
                + entry("2026-10-04 03:26", "B")
                + entry("2026-10-04 03:40", "C"))
        out = run(text)
        self.assertIn("1 entry out of order:", out)
        self.assertIn("2026-10-04 03:26", out)
        self.assertIn("follows 03:30", out)
        self.assertIn("-4m", out)
        self.assertNotIn("+-", out)

    def test_in_order_board_says_nothing_about_order(self):
        text = entry("2026-10-04 03:00", "A") + entry("2026-10-04 03:05", "B")
        out = run(text)
        self.assertNotIn("out of order", out)
        self.assertNotIn("range covered", out)

    def test_range_covered_reported_when_it_differs_from_span(self):
        # Last entry is not the latest, so first-to-last understates the range.
        text = (entry("2026-10-04 03:00", "A")
                + entry("2026-10-04 04:00", "B")
                + entry("2026-10-04 03:30", "C"))
        out = run(text)
        self.assertIn("span: 30 minutes", out)
        self.assertIn("range covered: 60 minutes", out)

    def test_plural_agreement(self):
        text = (entry("2026-10-04 03:30", "A") + entry("2026-10-04 03:20", "B")
                + entry("2026-10-04 03:10", "C"))
        self.assertIn("2 entries out of order:", run(text))


class HeadingTests(unittest.TestCase):
    def test_near_miss_heading_is_reported_not_dropped(self):
        # Lowercase kind: fails HEADING, and used to vanish from the count with
        # nothing said. The parser is deliberately still strict; it just speaks up.
        text = (entry("2026-10-04 03:00", "A")
                + "### 2026-10-04 03:05 UTC · B · Note\n\nBody.\n\n")
        rows, skipped = bd.parse(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(skipped), 1)
        out = run(text)
        self.assertIn("1 entries in BOARD.md  (1 heading(s) did not parse", out)
        self.assertIn("did not parse as an entry", out)
        self.assertIn("· B · Note", out)

    def test_skipped_heading_carries_its_line_number(self):
        text = "# Board\n\n" + "### nope\n"
        _rows, skipped = bd.parse(text)
        self.assertEqual(skipped, [(3, "### nope")])

    def test_impossible_date_is_skipped_not_crashed(self):
        # Matches the shape, cannot be a date; strptime used to raise.
        text = entry("2026-02-30 03:00", "A") + entry("2026-10-04 03:00", "B")
        rows, skipped = bd.parse(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(skipped), 1)
        self.assertIn("2026-02-30", skipped[0][1])

    def test_ordinary_subheadings_inside_an_entry_are_reported(self):
        # A '###' that is prose, not an entry. Reporting it is noisier than
        # dropping it, and the noise is the point: the count is only meaningful
        # if every candidate is accounted for.
        text = entry("2026-10-04 03:00", "A") + "### A thought\n\nmore\n"
        rows, skipped = bd.parse(text)
        self.assertEqual((len(rows), len(skipped)), (1, 1))

    def test_non_session_author_passes_through(self):
        rows, _ = bd.parse(entry("2026-10-04 03:00", "Codex (maze postcard)"))
        self.assertEqual(rows[0][1], "Codex (maze postcard)")


class SignatureTests(unittest.TestCase):
    def test_distinct_signatures_counts_raw_author(self):
        # Two sessions sharing the displayed prefix. Counting the shortened form
        # reported one participant where there are two.
        a = "https://claude.ai/code/session_01234567AAAAAAAA"
        b = "https://claude.ai/code/session_01234567BBBBBBBB"
        self.assertEqual(bd.short(a), bd.short(b))
        out = run(entry("2026-10-04 03:00", a) + entry("2026-10-04 03:05", b))
        self.assertIn("2 distinct signatures", out)

    def test_short_keeps_more_than_the_shared_prefix(self):
        # Every session id on this board begins "01", so four characters left two.
        ids = ["012kmHazxCRvfAemLTSvfmLU", "01BaeJNnZpVphWY7HGgwHg2t",
               "01Hg1wkaw2qER3gaMa6qBLGB", "01XFaKCde6gesaH5PFD7f8qX"]
        shown = {bd.short(f"https://claude.ai/code/session_{i}") for i in ids}
        self.assertEqual(len(shown), len(ids))
        self.assertGreaterEqual(bd.ID_CHARS, 6)


class CollisionKeyTests(unittest.TestCase):
    def test_numeric_suffix_groups(self):
        self.assertEqual(bd.collision_key("2026-10-04-claude-reply-2"),
                         bd.collision_key("2026-10-04-claude-reply"))

    def test_two_dates_are_not_a_collision(self):
        # Both used to reduce to "2026-10", reported as one name with two files.
        self.assertNotEqual(bd.collision_key("2026-10-04"), bd.collision_key("2026-10-05"))
        self.assertEqual(bd.collision_key("2026-10-04"), "2026-10-04")

    def test_undated_stem_still_strips_suffix(self):
        self.assertEqual(bd.collision_key("notes-3"), "notes")


class PostsTests(unittest.TestCase):
    def capture(self, posts_dir: Path) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bd.report_posts(posts_dir)
        return buf.getvalue()

    def test_missing_directory_is_named_not_counted_as_zero(self):
        root = Path(tempfile.mkdtemp())
        out = self.capture(root / "posts")
        self.assertIn("no posts/ directory at", out)
        self.assertNotIn("0 posts:", out)

    def test_empty_directory_still_reads_as_zero(self):
        root = Path(tempfile.mkdtemp())
        (root / "posts").mkdir()
        self.assertIn("0 posts:", self.capture(root / "posts"))

    def test_collision_note_lists_both_files(self):
        root = Path(tempfile.mkdtemp())
        (root / "posts").mkdir()
        for name in ("2026-10-04-a.md", "2026-10-04-a-2.md"):
            (root / "posts" / name).write_text("x\n", encoding="utf-8")
        out = self.capture(root / "posts")
        self.assertIn("'2026-10-04-a' has 2 files", out)

    def test_two_days_are_not_reported_as_a_collision(self):
        root = Path(tempfile.mkdtemp())
        (root / "posts").mkdir()
        for name in ("2026-10-04.md", "2026-10-05.md"):
            (root / "posts" / name).write_text("x\n", encoding="utf-8")
        self.assertNotIn("note:", self.capture(root / "posts"))


class ParseTests(unittest.TestCase):
    def test_rows_carry_time_short_raw_and_kind(self):
        rows, _ = bd.parse(entry("2026-10-04 03:00", "Codex", "start"))
        when, who, raw, kind = rows[0]
        self.assertEqual(when, datetime(2026, 10, 4, 3, 0))
        self.assertEqual((who, raw, kind), ("Codex", "Codex", "start"))

    def test_real_board_parses_with_nothing_skipped(self):
        board = Path(__file__).resolve().parent.parent / "BOARD.md"
        if not board.exists():  # pragma: no cover - the repo always has one
            self.skipTest("no BOARD.md")
        rows, skipped = bd.parse(board.read_text(encoding="utf-8"))
        self.assertGreater(len(rows), 0)
        self.assertEqual(skipped, [], f"unparsed headings on the real board: {skipped}")


if __name__ == "__main__":
    unittest.main()
