import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_stamps as cs  # noqa: E402

UTC = timezone.utc


def at(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


class CheckTests(unittest.TestCase):
    def test_flags_only_stamps_ahead_of_their_commit(self):
        lines = [
            (1, "# Board", at("2026-10-04 06:00")),
            (3, "### 2026-10-04 06:10 UTC · a · note", at("2026-10-04 06:10")),  # exact
            (5, "### 2026-10-04 06:12 UTC · b · note", at("2026-10-04 06:11")),  # within tolerance
            (7, "### 2026-10-04 07:20 UTC · c · end", at("2026-10-04 06:38")),   # ahead by 42
        ]
        entries, ahead, late = cs.check(lines)
        self.assertEqual(entries, 3)
        self.assertEqual([f[0] for f in ahead], [7])
        self.assertEqual(late, [])

    def test_notes_entries_committed_long_after_their_stamp(self):
        lines = [(2, "### 2026-10-04 05:00 UTC · a · note", at("2026-10-04 06:30"))]
        _, ahead, late = cs.check(lines)
        self.assertEqual(ahead, [])
        self.assertEqual([f[0] for f in late], [2])

    def test_ignores_non_headings_and_impossible_dates(self):
        lines = [
            (1, "#### 2026-10-04 09:00 UTC · not an entry", at("2026-10-04 06:00")),
            (2, "  ### 2026-10-04 09:00 UTC · indented, not a heading", at("2026-10-04 06:00")),
            (3, "### 2026-02-31 09:00 UTC · impossible date", at("2026-10-04 06:00")),
        ]
        self.assertEqual(cs.check(lines), (0, [], []))


class GitTests(unittest.TestCase):
    """Run blame against a real throwaway repository with controlled commit times."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, when=None):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        if when:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when + " +0000"
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, env=env)

    def append(self, text, when):
        board = self.repo / "BOARD.md"
        board.write_text((board.read_text() if board.exists() else "# Board\n") + text, encoding="utf-8")
        self.git("add", "BOARD.md")
        self.git("commit", "-q", "-m", "entry", when=when)

    def test_each_heading_is_compared_with_the_commit_that_added_it(self):
        self.append("\n### 2026-10-04 06:10 UTC · a · note\n\nfine\n", "2026-10-04T06:10:30")
        self.append("\n### 2026-10-04 07:20 UTC · b · end\n\nahead\n", "2026-10-04T06:38:00")
        self.append("\n### 2026-10-04 06:40 UTC · c · note\n\nfine, and later\n", "2026-10-04T06:41:00")
        entries, ahead, late = cs.check(cs.blame(self.repo, "HEAD"))
        self.assertEqual(entries, 3)
        self.assertEqual(len(ahead), 1)
        self.assertIn("· b ·", ahead[0][1])
        self.assertEqual(ahead[0][3], at("2026-10-04 06:38"))
        self.assertEqual(late, [])

    def test_the_finding_does_not_decay_when_later_commits_arrive(self):
        self.append("\n### 2026-10-04 07:20 UTC · b · end\n", "2026-10-04T06:38:00")
        self.append("\n### 2026-10-04 09:00 UTC · c · note\n", "2026-10-04T09:00:00")
        _, ahead, _ = cs.check(cs.blame(self.repo, "HEAD"))
        self.assertEqual([f[1] for f in ahead], ["### 2026-10-04 07:20 UTC · b · end"])


if __name__ == "__main__":
    unittest.main()
