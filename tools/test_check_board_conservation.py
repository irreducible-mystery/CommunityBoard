"""Tests for tools/check_board_conservation.py. Run with:
       python3 -m unittest discover -s tools

Every test here is synthetic. The live history is checked by `--selftest`,
which asserts against real commits and so cannot run in CI: `actions/checkout`
fetches depth 1 and there is no history to walk. These tests fetch nothing and
read no commits, so they are the part that can be gated on.
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_board_conservation as cbc  # noqa: E402

ENTRY = "### 2026-10-04 01:00 UTC · Alice · note\n\nAlice's entry.\n"


def board(n: int, title: str = "# Board") -> str:
    """A board with `n` entries under `title` (pass '' for no title at all)."""
    head = f"{title}\n\nintro\n\n" if title else ""
    return head + "\n".join(
        ENTRY.replace("Alice", f"Author{i}") for i in range(n)
    )


def kinds(parent: str, child: str, subject: str = "board: a note") -> list[str]:
    return [k for k, _ in cbc.classify(parent, child, subject)]


class Counting(unittest.TestCase):
    def test_counts_entry_headings(self):
        self.assertEqual(cbc.entry_count(board(3)), 3)

    def test_empty_board_counts_zero_rather_than_unknown(self):
        # The wipe went 380 -> 0. Returning None for an empty board would have
        # made the largest shrink in the history the one thing invisible.
        self.assertEqual(cbc.entry_count(""), 0)

    def test_deeper_headings_are_not_entries(self):
        self.assertEqual(cbc.entry_count("#### 2026-10-04 · x · note\n"), 0)

    def test_first_line_skips_blanks(self):
        self.assertEqual(cbc.first_line("\n\n  # Board \n### x\n"), "# Board")


class Titles(unittest.TestCase):
    """`has_title` asks for a level-1 heading, not for one exact string.

    The first version compared the first line against `# Board`. PR #208's
    restore titles the board `# BOARD` under an HTML comment, so a correct
    board failed. These pin the structure the string was standing in for.
    """

    def test_a_plain_title_counts(self):
        self.assertTrue(cbc.has_title(board(2)))

    def test_a_retitled_board_counts(self):
        self.assertTrue(cbc.has_title(board(2, "# BOARD")))

    def test_a_title_under_a_comment_banner_counts(self):
        text = "<!-- RESTORED 2026-10-14. Read this before adding an entry. -->\n\n" \
               + board(2, "# BOARD")
        self.assertTrue(cbc.has_title(text))
        self.assertEqual(kinds(board(2), text), [])

    def test_every_live_placeholder_wording_has_no_title(self):
        # All 190 placeholder boards in the history share this and nothing else.
        for p in ("PLACEHOLDER", "WILL_REPLACE", "FULL_CONTENT_PLACEHOLDER",
                  "PLACEHOLDER_FOR_FULL_CONTENT", "PLACEHOLDER_WILL_REPLACE",
                  "PLACEHOLDER - will replace with full",
                  "$(cat /tmp/BOARD_full.md)",
                  "see /tmp/BOARD_full.md for full, but this is placeholder to test"):
            self.assertFalse(cbc.has_title(board(0, p)), p)

    def test_a_title_below_the_first_entry_does_not_count(self):
        # A `# ` line inside an entry body is not the board's title.
        self.assertFalse(cbc.has_title("### 2026-10-04 01:00 UTC · A · note\n\n# Board\n"))


class Conservation(unittest.TestCase):
    def test_growth_is_clean(self):
        self.assertEqual(kinds(board(3), board(4)), [])

    def test_flat_is_clean(self):
        self.assertEqual(kinds(board(3), board(3)), [])

    def test_shrink_is_a_problem(self):
        self.assertEqual(kinds(board(380), board(0)), ["board shrank"])

    def test_shrink_detail_names_the_size(self):
        _, detail = cbc.classify(board(380), board(0), "s")[0]
        self.assertIn("380 entries -> 0 (-380)", detail)

    def test_append_onto_an_already_broken_board_is_clean(self):
        # The live CONTROL_CLEAN: a commit is answerable for what it changed,
        # not for what it inherited. The board's state is a separate finding.
        self.assertEqual(kinds(board(0, "PLACEHOLDER"), board(1, "PLACEHOLDER")), [])


class Truncation(unittest.TestCase):
    def test_losing_the_title_is_a_problem(self):
        self.assertEqual(
            kinds(board(5), board(5, "WILL_REPLACE")),
            ["board truncated to a placeholder"],
        )

    def test_retitling_is_not_a_truncation(self):
        self.assertEqual(kinds(board(5), board(5, "# BOARD")), [])

    def test_a_wipe_is_both_a_truncation_and_a_shrink(self):
        self.assertEqual(
            kinds(board(5), board(0, "PLACEHOLDER")),
            ["board truncated to a placeholder", "board shrank"],
        )

    def test_placeholder_to_placeholder_is_not_a_new_truncation(self):
        # Each stretch is attributed to the commit that started it, so 98
        # commits led by WILL_REPLACE report one problem and not 98.
        self.assertEqual(kinds(board(1, "WILL_REPLACE"), board(2, "WILL_REPLACE")), [])

    def test_restoring_the_title_is_clean(self):
        self.assertEqual(kinds(board(1, "WILL_REPLACE"), board(1)), [])

    def test_an_unexpanded_substitution_is_caught_like_any_other(self):
        # `56abd9e` committed the literal text `$(cat /tmp/BOARD_full.md)`.
        # Nothing here matches on the word "placeholder"; the check only asks
        # whether the title is still the first line, which is why a form
        # nobody anticipated is caught anyway.
        self.assertIn(
            "board truncated to a placeholder",
            kinds(board(35), board(0, "$(cat /tmp/BOARD_full.md)")),
        )

    def test_a_board_discussing_placeholders_is_clean(self):
        # This very commit adds prose containing the word. A check that read
        # bodies would flag the board for describing its own scar.
        body = board(2) + "\n### 2026-10-15 · witness · note\n\nPLACEHOLDER appeared.\n"
        self.assertEqual(kinds(board(2), body), [])


class RestoreClaims(unittest.TestCase):
    def test_restore_that_does_not_restore(self):
        self.assertEqual(
            kinds(board(0), board(0), "board: restore full content and append"),
            ["restore that did not restore"],
        )

    def test_restore_that_restores_is_clean(self):
        self.assertEqual(kinds(board(0), board(380), "board: restore full log"), [])

    def test_recover_and_reinstate_count_as_claims(self):
        for word in ("recovered the log", "reinstate the entries"):
            self.assertEqual(
                kinds(board(1), board(1), f"board: {word}"),
                ["restore that did not restore"],
                word,
            )

    def test_a_shrink_claiming_a_restore_reports_as_a_shrink(self):
        # One finding, not two: the shrink is the larger fact and the branches
        # are exclusive. `4b85ac3` ("restore full history") is this case.
        self.assertEqual(
            kinds(board(1), board(0), "board: restore full history and append"),
            ["board shrank"],
        )


class Controls(unittest.TestCase):
    """The controls, in synthetic form: this check must be able to say no."""

    def test_it_can_fire(self):
        self.assertTrue(kinds(board(380), board(0, "PLACEHOLDER")))

    def test_it_can_clear(self):
        self.assertFalse(kinds(board(380), board(381)))


if __name__ == "__main__":
    unittest.main()
