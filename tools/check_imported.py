#!/usr/bin/env python3
"""check_imported.py - keep imported/ to what its ledger says it is.

imported/ holds work by sessions and people who cannot reach GitHub, brought in
by a session that can. Whole sandboxes tend to come along with such work:
browser profiles, tunnel data, agent hooks, nested git repositories,
installers. This check is the allow-list that keeps those out, and it makes
sure every file is accounted for in imported/LEDGER.md.

It fails when a file under imported/:
  - has a name or directory starting with "." (hidden), or is inside a
    directory named .git, node_modules or __pycache__;
  - has a suffix not in ALLOWED;
  - is executable (mode +x) or a symlink;
  - is larger than MAX_BYTES;
  - is not listed in imported/LEDGER.md, as a table row starting
    | `folder/file` |  (paths mentioned in prose don't count).
It also fails when the ledger lists a file that is not there.

It reads files and never runs them. Python in imported/ is also read by
tools/check_code.py.

Usage:
    python3 tools/check_imported.py [repo-root]
Exit status: 0 when nothing is wrong, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED = {".md", ".txt", ".pdf", ".json", ".py", ".lean"}
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
MAX_BYTES = 2_000_000
LEDGER = "LEDGER.md"
LISTED = re.compile(r"^\|\s*`([^`\s]+/[^`\s]+)`\s*\|", re.MULTILINE)


def problems(root: Path) -> list[str]:
    base = root / "imported"
    if not base.is_dir():
        return []
    out: list[str] = []
    ledger_path = base / LEDGER
    listed: set[str] = set()
    if ledger_path.is_file():
        listed = set(LISTED.findall(ledger_path.read_text(encoding="utf-8")))
    else:
        out.append(f"imported/{LEDGER} is missing")
    present: set[str] = set()
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base).as_posix()
        parts = rel.split("/")
        if any(part in SKIP_DIRS for part in parts):
            out.append(f"imported/{rel}: inside a {'/'.join(d for d in parts if d in SKIP_DIRS)} directory")
            continue
        if any(part.startswith(".") for part in parts):
            out.append(f"imported/{rel}: hidden name")
            continue
        if p.is_symlink():
            out.append(f"imported/{rel}: symlink")
            continue
        if p.is_dir():
            continue
        if rel in (LEDGER, "README.md"):
            continue
        present.add(rel)
        if p.suffix.lower() not in ALLOWED:
            out.append(f"imported/{rel}: suffix {p.suffix or '(none)'} not in {sorted(ALLOWED)}")
        if p.stat().st_mode & 0o111:
            out.append(f"imported/{rel}: executable bit set")
        if p.stat().st_size > MAX_BYTES:
            out.append(f"imported/{rel}: {p.stat().st_size} bytes, over {MAX_BYTES}")
        if ledger_path.is_file() and rel not in listed:
            out.append(f"imported/{rel}: not listed in {LEDGER}")
    for rel in sorted(listed - present):
        out.append(f"{LEDGER} lists `{rel}` but there is no such file")
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    found = problems(root)
    for line in found:
        print(f"  {line}")
    n = sum(1 for p in (root / "imported").rglob("*") if p.is_file()) if (root / "imported").is_dir() else 0
    print(f"{n} file(s) under imported/, {len(found)} problem(s).")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
