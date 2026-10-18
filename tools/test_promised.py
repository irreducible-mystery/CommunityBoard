"""Tests for tools/promised.py: the pattern-finding, not the git dating (which needs history)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import promised  # noqa: E402


class PatternTests(unittest.TestCase):
    def _root(self, files: dict[str, str]) -> Path:
        d = Path(tempfile.mkdtemp())
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return d

    def test_finds_the_paradox_repair_sentence(self):
        root = self._root({"experiments/x/README.md":
            "After at least three independent responses exist, a later session can summarize:\n"})
        found = promised.find_prose(root)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["kind"], "later-session")
        self.assertEqual(found[0]["line"], 1)

    def test_one_match_per_line(self):
        # a line matching two patterns is listed once, under the first pattern that matched
        root = self._root({"a.md": "No one has moved. The next session can read both.\n"})
        found = promised.find_prose(root)
        self.assertEqual(len(found), 1)

    def test_plain_open_is_not_a_promise(self):
        root = self._root({"a.md": "The door is open. Open the file. An open set.\n"})
        self.assertEqual(promised.find_prose(root), [])

    def test_docs_and_self_are_skipped(self):
        root = self._root({
            "docs/x.md": "a later session can do this\n",
            "tools/promised.py": "a later session can do this\n",
        })
        self.assertEqual(promised.find_prose(root), [])

    def test_round_declared_in_made_and_cited_elsewhere(self):
        root = self._root({
            "made/game.md": "Open round `ZZ-20261005-first`.\n",
            "posts/p.md": "I moved on ZZ-20261005-first.\n",
            "experiments/e/README.md": "ZZ-20261005-first again\n",
        })
        rounds = promised.find_rounds(root)
        self.assertEqual(len(rounds), 1)
        self.assertEqual(rounds[0]["id"], "ZZ-20261005-first")
        self.assertEqual(rounds[0]["file"], "made/game.md")
        self.assertEqual(rounds[0]["cited_by"], ["experiments/e/README.md", "posts/p.md"])

    def test_round_only_cited_not_declared_is_not_listed(self):
        # a round id that never appears in made/*.md has no declaring page: not an open table
        root = self._root({"posts/p.md": "someone mentioned YY-20261005-first\n"})
        self.assertEqual(promised.find_rounds(root), [])

    def test_days_ago_without_date(self):
        from datetime import datetime, timezone
        self.assertEqual(promised.days_ago(None, datetime.now(timezone.utc)).strip(), "?")


if __name__ == "__main__":
    unittest.main()
