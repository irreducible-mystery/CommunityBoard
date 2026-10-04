#!/usr/bin/env python3
"""check_made.py - keep made/ honest about its own promise.

made/README.md says each item should be "openable or runnable on its own,
ideally with no dependencies". That is a claim the repo makes about itself,
and until now nothing checked it. This script checks two things:

  1. Self-contained. No made/*.html reaches the network: no remote src,
     no remote <link href>, no @import, no url(...) that points off-machine,
     no fetch / XMLHttpRequest / importScripts / sendBeacon.

  2. Indexed. Every file in made/ (except README.md) is named in
     made/README.md, and every file named there actually exists.

It only reads. Exit status is 0 when everything passes, 1 when something is
flagged. Standard library only, so it runs anywhere the repo does.

Usage:
    python3 tools/check_made.py [repo-root]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A reference is "external" if the browser would have to leave the machine.
EXTERNAL = re.compile(r"^(?:https?:)?//", re.IGNORECASE)

# Things a page loads while rendering.
SRC = re.compile(r"""(?is)\bsrc\s*=\s*["']([^"']*)["']""")
LINK_TAG = re.compile(r"(?is)<link\b[^>]*>")
LINK_HREF = re.compile(r"""(?is)\bhref\s*=\s*["']([^"']*)["']""")
CSS_IMPORT = re.compile(r"""(?i)@import\s+(?:url\()?\s*["']?([^"')\s;]+)""")
CSS_URL = re.compile(r"""(?i)url\(\s*["']?([^"')]+?)["']?\s*\)""")
NETWORK_CALL = re.compile(r"(?i)\b(fetch|XMLHttpRequest|importScripts|sendBeacon)\b")

# File names the index might mention, e.g. `murmuration.html`.
INDEX_NAME = re.compile(r"`([A-Za-z0-9._-]+\.(?:html|py|js|css|md|svg))`")


def is_external(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("data:", "#")):
        return False
    return bool(EXTERNAL.match(value))


def lineno(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_html(path: Path) -> list[tuple[int, str, str]]:
    """Return (line, kind, detail) for every off-machine reference in one page."""
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[tuple[int, str, str]] = []

    for m in SRC.finditer(text):
        if is_external(m.group(1)):
            problems.append((lineno(text, m.start()), "src", m.group(1)))

    for tag in LINK_TAG.finditer(text):
        for m in LINK_HREF.finditer(tag.group(0)):
            if is_external(m.group(1)):
                problems.append((lineno(text, tag.start()), "<link href>", m.group(1)))

    for m in CSS_IMPORT.finditer(text):
        if is_external(m.group(1)):
            problems.append((lineno(text, m.start()), "@import", m.group(1)))

    for m in CSS_URL.finditer(text):
        if is_external(m.group(1)):
            problems.append((lineno(text, m.start()), "url()", m.group(1)))

    for m in NETWORK_CALL.finditer(text):
        problems.append((lineno(text, m.start()), "network call", m.group(1)))

    return problems


def check(root: Path) -> int:
    made = root / "made"
    readme = made / "README.md"
    if not made.is_dir():
        print(f"no made/ directory under {root}")
        return 1

    pages = sorted(p for p in made.glob("*.html"))
    items = sorted(p for p in made.iterdir() if p.is_file() and p.name != "README.md")

    print("made/ self-containment check")
    problems_total = 0
    for page in pages:
        found = scan_html(page)
        if found:
            problems_total += len(found)
            print(f"  {page.name}")
            for line, kind, detail in found:
                print(f"      line {line}: {kind}: {detail}")
        else:
            print(f"  {page.name:<28} ok")
    if not pages:
        print("  (no .html pages)")

    print("\nmade/ index check")
    if not readme.exists():
        print("  made/README.md is missing")
        problems_total += 1
    else:
        index_text = readme.read_text(encoding="utf-8", errors="replace")
        named = set(INDEX_NAME.findall(index_text))
        missing = [p.name for p in items if p.name not in index_text]
        stale = sorted(n for n in named if not (made / n).exists())
        for p in items:
            mark = "ok" if p.name not in missing else "not in index"
            print(f"  {p.name:<28} {mark}")
        for name in missing:
            problems_total += 1
            print(f"  missing from made/README.md: {name}")
        for name in stale:
            problems_total += 1
            print(f"  named in made/README.md but absent: {name}")

    print(f"\n{len(pages)} page(s) checked, {problems_total} problem(s).")
    return 1 if problems_total else 0


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
