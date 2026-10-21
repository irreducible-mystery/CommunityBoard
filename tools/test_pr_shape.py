import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_shape as ps  # noqa: E402


def run(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-C", repo, *args], check=True,
                          capture_output=True, text=True, env=env).stdout.strip()


def commit(repo, path, text, msg):
    p = Path(repo, path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    run(repo, "add", "-A")
    run(repo, "commit", "-qm", msg)


class ShapeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        run(self.repo, "init", "-q", "-b", "main")
        commit(self.repo, "made/README.md", "a\nb\nc\n", "base")
        self.cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def branch(self, name, path, text):
        run(self.repo, "checkout", "-qb", name, "main")
        commit(self.repo, path, text, name)
        run(self.repo, "checkout", "-q", "main")

    def test_additive_pr_is_clean(self):
        self.branch("add", "made/x.py", "x\n")
        r = ps.shape("main", "add")
        self.assertEqual((r["merge"], r["added"], r["modified"], r["deleted"]), ("clean", 1, 0, 0))

    def test_conflict_names_the_path(self):
        self.branch("one", "made/README.md", "a\nONE\nc\n")
        commit(self.repo, "made/README.md", "a\nMAIN\nc\n", "main moves")
        r = ps.shape("main", "one")
        self.assertEqual(r["merge"], "conflict")
        self.assertEqual(r["conflicts"], ["made/README.md"])
        self.assertEqual(r["behind"], "1")

    def test_merged_pr_reads_in_base_not_clean(self):
        self.branch("done", "made/y.py", "y\n")
        run(self.repo, "merge", "-q", "--no-edit", "done")
        self.assertEqual(ps.shape("main", "done")["merge"], "in-base")

    def test_unrelated_history_is_no_base_not_conflict(self):
        # What a shallow clone looks like to merge-base: no shared commit.
        run(self.repo, "checkout", "-q", "--orphan", "stray")
        commit(self.repo, "other.txt", "o\n", "stray")
        run(self.repo, "checkout", "-q", "main")
        self.assertEqual(ps.shape("main", "stray")["merge"], "no-base")

    def test_flags_board_rules_and_ci(self):
        _, _, _, touches = ps.classify(["A\tboard/entries/0001.md", "M\tRULES.md",
                                        "M\t.github/workflows/x.yml", "M\tmade/README.md"])
        self.assertEqual(touches, ["board", "rules", "ci"])
        self.assertEqual(ps.classify(["M\tmade/board-rate.py"])[3], [])

    def test_main_prints_a_summary(self):
        self.branch("add", "made/x.py", "x\n")
        out = StringIO()
        with redirect_stdout(out):
            self.assertEqual(ps.main(["--base", "main", "add"]), 0)
        self.assertIn("1 ref(s): 1 clean", out.getvalue())


if __name__ == "__main__":
    unittest.main()
