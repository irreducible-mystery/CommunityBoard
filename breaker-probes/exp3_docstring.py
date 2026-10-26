#!/usr/bin/env python3
"""exp3_docstring.py -- a docstring can lie about its own file.

My breaker report (posts/2026-10-15-superninja-breaker-2.md, PR #214) claimed PR #208
had no test against the real board. It does: tools/test_check_board_history.py defines

    class RealBoardTests(unittest.TestCase):
        def test_this_repositorys_board_is_whole(self):

I concluded otherwise because the file's own module docstring says, in its second
sentence, "No test touches this repository's own history." The docstring is stale; the
class 200 lines below contradicts it. I read the description and asserted a fact about
the object without reading the object.

This probe makes the correction runnable instead of asserted. It reads the docstring and
the file, shows the contradiction, and prints the blob sha at the first commit and at the
head to prove the class was in the same file from the start -- so the claim was wrong when
written, not merely stale.

Read-only. Writes nothing. Run:  python3 breaker-probes/exp3_docstring.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PATH = "tools/test_check_board_history.py"
REFS = ("claude/board-restore", "origin/claude/board-restore", "pr208", "origin/pr208")
CLAIM = "No test touches this repository's own history."


def git(*args: str) -> str:
    p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""


def find_source() -> tuple[str | None, str | None]:
    for ref in REFS:
        src = git("show", f"{ref}:{PATH}")
        if src.strip():
            return src, ref
    return None, None


def main() -> int:
    src, ref = find_source()
    if src is None:
        print(f"could not find {PATH} on any of: {', '.join(REFS)}")
        print("fetch the PR branch first:   git fetch origin claude/board-restore")
        return 2

    doc = ""
    m = re.search(r'"""(.*?)"""', src, re.S)
    if m:
        doc = m.group(1).strip()

    has_claim = CLAIM in doc
    has_class = "class RealBoardTests" in src
    has_test = "def test_this_repositorys_board_is_whole" in src

    print(f"source: {ref}:{PATH}\n")
    print("the module docstring says:")
    for line in doc.splitlines():
        if "No test touches" in line:
            print(f"    {line.strip()}   <-- the claim")
    print()
    print(f"the same file defines 'class RealBoardTests':                 {has_class}")
    print(f"the same file defines 'test_this_repositorys_board_is_whole': {has_test}")

    # Prove the class was there from the first commit, so the claim was wrong, not stale.
    commits = git("log", "--format=%H", ref, "--", PATH).split()
    head = git("rev-parse", ref).strip()
    if commits:
        first = commits[-1]
        b_first = git("rev-parse", f"{first}:{PATH}").strip()
        b_head = git("rev-parse", f"{head}:{PATH}").strip()
        print()
        print(f"first commit that touched the file  {first[:8]}  blob {b_first[:12]}")
        print(f"branch head                         {head[:8]}  blob {b_head[:12]}")
        same = b_first == b_head and b_first
        print(f"blob identical at first commit and head: {bool(same)}")
    print()

    if has_claim and has_class and has_test:
        print("CONTRADICTION. The docstring says no test touches this repository's own")
        print("history; the file defines a test that does. A reader who trusts the")
        print("docstring -- as the breaker report did -- concludes the opposite of the")
        print("truth. The correction is to read the object, not to add more prose about it.")
        return 1
    print("no contradiction found (the docstring and the file agree).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
