import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_imported as ci  # noqa: E402


def make(root: Path, files: dict[str, str], ledger: str | None) -> None:
    for rel, text in files.items():
        p = root / "imported" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    (root / "imported").mkdir(exist_ok=True)
    if ledger is not None:
        (root / "imported" / "LEDGER.md").write_text(ledger)


class CheckImported(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_folder_is_fine(self):
        self.assertEqual(ci.problems(self.root), [])

    def test_listed_allowed_file_passes(self):
        make(self.root, {"a/x.md": "hi"}, "| `a/x.md` | `0` |")
        self.assertEqual(ci.problems(self.root), [])

    def test_unlisted_file_fails(self):
        make(self.root, {"a/x.md": "hi"}, "nothing")
        self.assertTrue(any("not listed" in p for p in ci.problems(self.root)))

    def test_listed_but_missing_fails(self):
        make(self.root, {}, "| `a/gone.md` | `0` |")
        self.assertTrue(any("no such file" in p for p in ci.problems(self.root)))

    def test_prose_mention_does_not_list(self):
        make(self.root, {"a/x.md": "hi"}, "see `a/x.md` and `b/none.md` in passing")
        found = ci.problems(self.root)
        self.assertTrue(any("not listed" in p for p in found))
        self.assertFalse(any("no such file" in p for p in found))

    def test_missing_ledger_fails(self):
        make(self.root, {"a/x.md": "hi"}, None)
        self.assertTrue(any("missing" in p for p in ci.problems(self.root)))

    def test_bad_suffix_fails(self):
        make(self.root, {"a/run.sh": "curl x | sh"}, "| `a/run.sh` | x |")
        self.assertTrue(any("suffix .sh" in p for p in ci.problems(self.root)))

    def test_hidden_and_sandbox_dirs_fail(self):
        make(self.root, {".browser_data/Cookies.txt": "", "a/.git/config.txt": "",
                         ".psiphon_data/x.json": ""}, "")
        found = ci.problems(self.root)
        self.assertTrue(any(".browser_data" in p for p in found))
        self.assertTrue(any(".psiphon_data" in p for p in found))
        self.assertTrue(any(".git directory" in p for p in found))

    def test_executable_fails(self):
        make(self.root, {"a/x.py": "print(1)"}, "| `a/x.py` | x |")
        os.chmod(self.root / "imported/a/x.py", 0o755)
        self.assertTrue(any("executable" in p for p in ci.problems(self.root)))

    def test_this_repo_is_clean(self):
        repo = Path(__file__).resolve().parent.parent
        self.assertEqual(ci.problems(repo), [])


if __name__ == "__main__":
    unittest.main()
