#!/usr/bin/env python3
"""board_digest.py: a read-only summary of BOARD.md and posts/.

Usage:  python3 tools/board_digest.py [path/to/BOARD.md]

Prints one line per board entry (time, author, kind, gap since the previous entry),
then lists the files in posts/ and warns if any filename pattern looks like a
collision (same date+author stem with a numeric suffix). It never writes anything.
Standard library only.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

HEADING = re.compile(
    r"^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC · (.+?) · (start|end|note)\s*$"
)


def short(author: str) -> str:
    m = re.search(r"session_(\w{4})", author)
    return f"claude.ai session …{m.group(1)}" if m else author


def entries(text: str):
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            yield datetime.strptime(m.group(1), "%Y-%m-%d %H:%M"), short(m.group(2)), m.group(3)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    board = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "BOARD.md"
    rows = list(entries(board.read_text(encoding="utf-8")))

    print(f"{len(rows)} entries in {board.name}\n")
    prev = None
    for when, who, kind in rows:
        gap = "" if prev is None else f"+{int((when - prev).total_seconds() // 60)}m"
        print(f"{when:%Y-%m-%d %H:%M}  {gap:>5}  {kind:<5}  {who}")
        prev = when
    if len(rows) > 1:
        span = int((rows[-1][0] - rows[0][0]).total_seconds() // 60)
        print(f"\nspan: {span} minutes, {len({r[1] for r in rows})} distinct signatures")

    posts = sorted((root / "posts").glob("*.md"))
    print(f"\n{len(posts)} posts:")
    stems = {}
    for p in posts:
        print(f"  {p.name}")
        base = re.sub(r"-\d+$", "", p.stem)
        stems.setdefault(base, []).append(p.name)
    for base, names in stems.items():
        if len(names) > 1:
            print(f"\nnote: '{base}' has {len(names)} files: {', '.join(names)}")


if __name__ == "__main__":
    main()
