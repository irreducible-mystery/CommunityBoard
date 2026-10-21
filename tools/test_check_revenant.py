#!/usr/bin/env python3
"""Tests for check_revenant.py.

Each test builds a throwaway git repository and asks the checker what it sees. No test touches
this repository's own history. Each protective case is paired with the mutation it should
catch, and one test replays the bug the first draft of the checker had: a generator that
yielded a commit before its diff lines were read, and so saw a clean history in a repository
with a known revenant.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_revenant as cr  # noqa: E402


def sh(cwd, *args):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


_KEEP = []  # hold temp dirs until interpreter exit; silences cleanup warnings mid-test


class Repo:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        _KEEP.append(self.tmp)
        self.path = Path(self.tmp.name)
        sh(self.path, "git", "init", "-q", "-b", "main")
        sh(self.path, "git", "config", "user.email", "t@example.invalid")
        sh(self.path, "git", "config", "user.name", "t")
        sh(self.path, "git", "config", "commit.gpgsign", "false")

    def write(self, name, text):
        (self.path / name).write_text(text)

    def commit(self, msg, **files):
        for name, text in files.items():
            self.write(name, text)
            sh(self.path, "git", "add", name)
        sh(self.path, "git", "commit", "-q", "--allow-empty", "-m", msg)
        return sh(self.path, "git", "rev-parse", "HEAD")

    def run(self, *args):
        old = os.getcwd()
        os.chdir(self.path)
        try:
            cr.blob_at.cache_clear()
            cr.is_ancestor.cache_clear()
            return cr.find_revenants("HEAD", None, None)
        finally:
            os.chdir(old)


class Linear(unittest.TestCase):
    def test_clean_history_has_no_revenants(self):
        r = Repo()
        r.commit("a", f="1\n")
        r.commit("b", f="1\n2\n")
        r.commit("c", f="1\n2\n3\n")
        self.assertEqual(r.run(), {})

    def test_stale_rewrite_is_a_revenant(self):
        """The #209 shape: a commit that writes the file whole from an old copy."""
        r = Repo()
        old = r.commit("a", f="1\n")
        r.commit("b", f="1\n2\n")
        back = r.commit("append a note, from a stale copy", f="1\n")
        found = r.run()
        self.assertEqual(list(found), ["f"])
        (h, _d, s, eh, _ed, _es), = found["f"]
        self.assertEqual(h, back)
        self.assertEqual(eh, old)
        self.assertIn("stale", s)

    def test_repeating_the_parent_is_not_a_change(self):
        """Committing the same bytes twice in a row is a no-op to git and to us."""
        r = Repo()
        r.commit("a", f="1\n")
        r.commit("b", f="1\n2\n")
        r.commit("nothing", g="x\n")  # f untouched
        self.assertEqual(r.run(), {})

    def test_delete_and_restore_is_a_revenant(self):
        r = Repo()
        r.commit("a", f="1\n")
        sh(r.path, "git", "rm", "-q", "f")
        sh(r.path, "git", "commit", "-q", "-m", "retire f")
        r.commit("bring it back", f="1\n")
        self.assertEqual(len(r.run().get("f", [])), 1)

    def test_only_the_named_path_is_reported(self):
        r = Repo()
        r.commit("a", f="1\n", g="1\n")
        r.commit("b", f="2\n", g="2\n")
        r.commit("c", f="1\n", g="1\n")
        old = os.getcwd()
        os.chdir(r.path)
        try:
            cr.blob_at.cache_clear(); cr.is_ancestor.cache_clear()
            self.assertEqual(list(cr.find_revenants("HEAD", "g", None)), ["g"])
        finally:
            os.chdir(old)


class Merges(unittest.TestCase):
    def test_merge_that_adopts_its_branch_is_not_a_revenant(self):
        """A merge whose result equals the branch tip did not return anywhere; it arrived.
        The first working draft reported 67 of these on made/README.md. Every ordinary
        merge was a 'revenant' of its own second parent."""
        r = Repo()
        r.commit("base", f="1\n")
        sh(r.path, "git", "checkout", "-q", "-b", "side")
        r.commit("side work", f="1\nside\n")
        sh(r.path, "git", "checkout", "-q", "main")
        r.commit("main work", g="x\n")
        sh(r.path, "git", "merge", "-q", "--no-ff", "-m", "merge side", "side")
        self.assertEqual(r.run(), {})

    def test_stale_write_on_a_branch_is_found_where_it_happened(self):
        """The quoin shape (8005afc / f040c91): the branch commit holds the stale blob, and
        the merge carries the regression onto main. Both are reported, at the commit that
        wrote it and at the merge that landed it."""
        r = Repo()
        stale = r.commit("base", f="line\n")
        r.commit("repair", f="line\n# heading\n")
        sh(r.path, "git", "checkout", "-q", "-b", "side")
        bad = r.commit("new game, README written from an old copy", f="line\n", game="g\n")
        sh(r.path, "git", "checkout", "-q", "main")
        r.commit("unrelated", other="o\n")
        sh(r.path, "git", "merge", "-q", "--no-ff", "-m", "merge side (checked PASS)", "side")
        merge = sh(r.path, "git", "rev-parse", "HEAD")
        found = r.run()["f"]
        commits = {h for h, *_ in found}
        self.assertIn(bad, commits)
        # The merge's f equals the side branch's f (a parent), so the merge itself is the
        # branch arriving, not a return. The return is charged to the commit that made it.
        self.assertNotIn(merge, commits)
        self.assertEqual({eh for *_, eh, _ed, _es in found}, {stale})

    def test_siblings_converging_on_the_same_bytes_are_not_revenants(self):
        """Two branches that independently produce identical content did not go back."""
        r = Repo()
        r.commit("base", f="1\n")
        sh(r.path, "git", "checkout", "-q", "-b", "a")
        r.commit("a", f="1\n2\n")
        sh(r.path, "git", "checkout", "-q", "main")
        sh(r.path, "git", "checkout", "-q", "-b", "b")
        r.commit("b", f="1\n2\n")
        sh(r.path, "git", "checkout", "-q", "main")
        sh(r.path, "git", "merge", "-q", "--no-ff", "-m", "merge a", "a")
        sh(r.path, "git", "merge", "-q", "--no-ff", "-m", "merge b", "b")
        self.assertEqual(r.run(), {})


class Instrument(unittest.TestCase):
    def test_reader_sees_the_diff_lines_of_every_commit(self):
        """Replays the first draft's bug. `touches` must yield a commit only after its raw
        lines are attached; a commit yielded early carries an empty dict and the checker
        reports a clean history for a repository with a known revenant."""
        r = Repo()
        r.commit("a", f="1\n")
        r.commit("b", f="2\n")
        r.commit("c", f="1\n")
        old = os.getcwd()
        os.chdir(r.path)
        try:
            commits = list(cr.touches("HEAD", None, None))
        finally:
            os.chdir(old)
        self.assertEqual(len(commits), 3)
        for _h, _p, _d, _s, changes in commits:
            self.assertIn("f", changes, "a commit was yielded with no diff attached")

    def test_exit_code_follows_findings(self):
        r = Repo()
        r.commit("a", f="1\n")
        r.commit("b", f="2\n")
        old = os.getcwd()
        os.chdir(r.path)
        try:
            self.assertEqual(cr.main(["--quiet"]), 0)
            r.commit("c", f="1\n")
            cr.blob_at.cache_clear(); cr.is_ancestor.cache_clear()
            self.assertEqual(cr.main(["--quiet"]), 1)
        finally:
            os.chdir(old)


if __name__ == "__main__":
    unittest.main()
