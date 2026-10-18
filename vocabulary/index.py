#!/usr/bin/env python3
"""
index.py — regenerate the table between the index markers in vocabulary/README.md
from the one-word-per-file entries beside it.

    python3 vocabulary/index.py          # rewrite the index in README.md
    python3 vocabulary/index.py --check  # exit 1 if README.md's index is stale

Each word file is `<word>.md` with a `**Short:**` line; the index shows word, short line, and
the `**From:**` line's first clause. Standard library, writes only README.md, only between
the markers, and only the generated table. Everything else in README.md is left alone.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
README = HERE / "README.md"
BEGIN, END = "<!-- index:begin -->", "<!-- index:end -->"


def field(text: str, name: str) -> str:
    m = re.search(rf"^\*\*{name}:\*\*\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def build() -> str:
    rows = []
    for p in sorted(HERE.glob("*.md")):
        if p.name == "README.md":
            continue
        t = p.read_text(encoding="utf-8")
        short = field(t, "Short")
        frm = field(t, "From").split(";")[0].split(". ")[0]
        later = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", t, re.M))
        rows.append((p.stem, short, frm, later))
    if not rows:
        return "\n_(no words yet)_\n"
    out = ["", "| word | short | from | later movements |", "|---|---|---|---:|"]
    for word, short, frm, later in rows:
        out.append(f"| [`{word}`]({word}.md) | {short} | {frm} | {later} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    text = README.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print("README.md has no index markers", file=sys.stderr)
        return 1
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + BEGIN + build() + END + tail
    if "--check" in argv:
        if new != text:
            print("vocabulary/README.md index is stale; run python3 vocabulary/index.py")
            return 1
        print("vocabulary index up to date")
        return 0
    README.write_text(new, encoding="utf-8")
    print(f"wrote index: {sum(1 for p in HERE.glob('*.md')) - 1} word(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
