#!/usr/bin/env python3
"""check_made.py - keep made/ honest about its own promise.

made/README.md says each item should be "openable or runnable on its own,
ideally with no dependencies". That is a claim the repo makes about itself,
and this script checks it:

  1. Self-contained. No HTML page under made/ (any depth) reaches the network:
     no remote src / srcset / <link href> / <object data> / poster, no @import
     or url(...) that points off-machine, no http(s)/ws(s) URL inside a
     JavaScript string, and no call to fetch / XMLHttpRequest / WebSocket /
     EventSource / importScripts / sendBeacon / dynamic import().

  2. Indexed. Every file under made/ (except README.md) is named in
     made/README.md as a backticked `name`, `sub/name` or [link](name), and
     every file named there exists.

It only reads. Exit status is 0 when everything passes, 1 when something is
flagged. Standard library only, so it runs anywhere the repo does.

Usage:
    python3 tools/check_made.py [repo-root]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

Problem = tuple[int, str, str]  # (line, kind, detail)

# A reference is "external" if the browser would have to leave the machine.
EXTERNAL = re.compile(r"^(?:(?:https?|wss?):)?//", re.IGNORECASE)

# Attributes a page loads while rendering.
LOAD_ATTR = re.compile(
    r"""(?is)\b(src|srcset|data|poster|action)\s*=\s*(?P<q>["'])(?P<v>.*?)(?P=q)"""
)
LINK_TAG = re.compile(r"(?is)<link\b[^>]*>")
LINK_HREF = re.compile(r"""(?is)\bhref\s*=\s*(?P<q>["'])(?P<v>.*?)(?P=q)""")
CSS_IMPORT = re.compile(r"""(?i)@import\s+(?:url\()?\s*["']?([^"')\s;]+)""")
CSS_URL = re.compile(r"""(?i)url\(\s*["']?([^"')]+?)["']?\s*\)""")

# Network APIs, matched as calls or constructors so prose such as
# "fetch the next frame" in a comment is not flagged.
NETWORK_CALL = re.compile(
    r"(?x)"
    r"\bfetch\s*\("
    r"|\bnew\s+(?:XMLHttpRequest|WebSocket|EventSource)\s*\("
    r"|\bimportScripts\s*\("
    r"|\bsendBeacon\s*\("
    r"|(?<![\w.])import\s*\(\s*[\"'`]\s*(?:(?:https?|wss?):)?//"
)

# Any absolute network URL inside a quoted JavaScript/HTML string.
URL_IN_STRING = re.compile(r"""["'`]\s*((?:https?|wss?)://[^"'`\s]+)""", re.IGNORECASE)

# How made/README.md names files: `name`, `sub/name`, or [text](name).
INDEX_CODE = re.compile(r"`([A-Za-z0-9._/-]+\.[A-Za-z0-9]+)`")
INDEX_LINK = re.compile(r"\]\(([A-Za-z0-9._/-]+\.[A-Za-z0-9]+)\)")


def is_external(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("data:", "#", "blob:", "about:")):
        return False
    return bool(EXTERNAL.match(value))


def lineno(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_html(path: Path) -> list[Problem]:
    """Return every off-machine reference found in one page."""
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[Problem] = []
    seen: set[tuple[int, str]] = set()

    def add(pos: int, kind: str, detail: str) -> None:
        key = (lineno(text, pos), detail)
        if key not in seen:
            seen.add(key)
            problems.append((lineno(text, pos), kind, detail))

    for m in LOAD_ATTR.finditer(text):
        attr, value = m.group(1).lower(), m.group("v")
        candidates = [c.strip().split()[0] for c in value.split(",") if c.strip()] if attr == "srcset" else [value]
        for c in candidates:
            if is_external(c):
                add(m.start(), attr, c)

    for tag in LINK_TAG.finditer(text):
        for m in LINK_HREF.finditer(tag.group(0)):
            if is_external(m.group("v")):
                add(tag.start(), "<link href>", m.group("v"))

    for m in CSS_IMPORT.finditer(text):
        if is_external(m.group(1)):
            add(m.start(), "@import", m.group(1))

    for m in CSS_URL.finditer(text):
        if is_external(m.group(1)):
            add(m.start(), "url()", m.group(1))

    for m in NETWORK_CALL.finditer(text):
        add(m.start(), "network call", m.group(0).strip())

    for m in URL_IN_STRING.finditer(text):
        add(m.start(), "url in string", m.group(1))

    return problems


def index_names(index_text: str) -> set[str]:
    return set(INDEX_CODE.findall(index_text)) | set(INDEX_LINK.findall(index_text))


def check(root: Path) -> int:
    made = root / "made"
    readme = made / "README.md"
    if not made.is_dir():
        print(f"no made/ directory under {root}")
        return 1

    items = sorted(
        p.relative_to(made).as_posix()
        for p in made.rglob("*")
        if p.is_file() and p.name != "README.md" and not any(part.startswith(".") for part in p.parts)
    )
    pages = [name for name in items if name.lower().endswith((".html", ".htm"))]

    print("made/ self-containment check")
    problems_total = 0
    for name in pages:
        found = scan_html(made / name)
        if found:
            problems_total += len(found)
            print(f"  {name}")
            for line, kind, detail in found:
                print(f"      line {line}: {kind}: {detail}")
        else:
            print(f"  {name:<28} ok")
    if not pages:
        print("  (no .html pages)")

    print("\nmade/ index check")
    if not readme.exists():
        print("  made/README.md is missing")
        problems_total += 1
    else:
        named = index_names(readme.read_text(encoding="utf-8", errors="replace"))
        # A file counts as indexed by its path from made/ or by its bare name.
        indexed = {n for n in items if n in named or Path(n).name in named}
        existing = set(items) | {Path(n).name for n in items}
        stale = sorted(n for n in named if n not in existing)
        for name in items:
            print(f"  {name:<28} {'ok' if name in indexed else 'not in index'}")
        for name in items:
            if name not in indexed:
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
