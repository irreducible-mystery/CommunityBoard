#!/usr/bin/env python3
"""check_made.py - keep made/ honest about its own promise.

made/README.md says each item should be "openable or runnable on its own,
ideally with no dependencies". That is a claim the repo makes about itself,
and this script checks it:

  1. Self-contained. No HTML page under made/ (any depth) *loads* anything
     from the network: no remote src / srcset / <link href> / <object data> /
     poster / form action, no @import or url(...) that points off-machine,
     and inside <script> bodies no fetch / XMLHttpRequest / WebSocket /
     EventSource / importScripts / sendBeacon / dynamic import() and no
     http(s)/ws(s) URL inside a string literal. Ordinary <a href> links out
     to the web are allowed: a link is not a dependency.

  2. Indexed. Every file under made/ (except README.md) is named in
     made/README.md as a backticked `name`, `sub/name` or [link](name), and
     every file named there exists.

The scanner is a heuristic. A clean result means none of the patterns above
were found, not a proof that a page can never reach the network.

It only reads. Exit status is 0 when everything passes, 1 when something is
flagged. Standard library only, so it runs anywhere the repo does.

Usage:
    python3 tools/check_made.py [repo-root]
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

Problem = tuple[int, str, str]  # (line, kind, detail)

# A reference is "external" if the browser would have to leave the machine.
EXTERNAL = re.compile(r"^\s*(?:(?:https?|wss?):)?//", re.IGNORECASE)

# Attributes whose value the browser loads while rendering.
LOAD_ATTRS = {"src", "srcset", "data", "poster", "action"}

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

# Any absolute network URL inside a quoted string literal (script bodies only).
URL_IN_STRING = re.compile(r"""["'`]\s*((?:https?|wss?)://[^"'`\s]+)""", re.IGNORECASE)

# How made/README.md names files: `name`, `sub/name`, or [text](name).
INDEX_CODE = re.compile(r"`([A-Za-z0-9._/-]+\.[A-Za-z0-9]+)`")
INDEX_LINK = re.compile(r"\]\(([A-Za-z0-9._/-]+\.[A-Za-z0-9]+)\)")


def is_external(value: str | None) -> bool:
    if not value:
        return False
    value = value.strip()
    if value.startswith(("data:", "#", "blob:", "about:")):
        return False
    return bool(EXTERNAL.match(value))


class _Scanner(HTMLParser):
    """Walk a page once, collecting off-machine references with line numbers.

    HTMLParser decodes character references in attribute values and accepts
    unquoted attributes, so `src=https://…` and `src="https&#58;//…"` are both
    seen as what the browser would see.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.problems: list[Problem] = []
        self._seen: set[tuple[int, str]] = set()
        self._in: str | None = None  # "script" | "style" | None
        self._block_start = 0
        self._block: list[str] = []

    def _add(self, line: int, kind: str, detail: str) -> None:
        key = (line, detail)
        if key not in self._seen:
            self._seen.add(key)
            self.problems.append((line, kind, detail))

    def _attr_check(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line = self.getpos()[0]
        for name, value in attrs:
            name = name.lower()
            if value is None:
                continue
            if name in LOAD_ATTRS:
                if name == "srcset":
                    parts = [c.strip().split()[0] for c in value.split(",") if c.strip()]
                else:
                    parts = [value]
                for p in parts:
                    if is_external(p):
                        self._add(line, name, p.strip())
            elif name == "href" and tag == "link" and is_external(value):
                self._add(line, "<link href>", value.strip())
            elif name == "style":
                self._scan_css(value, line)

    def _scan_css(self, css: str, base_line: int) -> None:
        for m in CSS_IMPORT.finditer(css):
            if is_external(m.group(1)):
                self._add(base_line + css.count("\n", 0, m.start()), "@import", m.group(1))
        for m in CSS_URL.finditer(css):
            if is_external(m.group(1)):
                self._add(base_line + css.count("\n", 0, m.start()), "url()", m.group(1))

    def _scan_js(self, js: str, base_line: int) -> None:
        for m in NETWORK_CALL.finditer(js):
            self._add(base_line + js.count("\n", 0, m.start()), "network call", m.group(0).strip())
        for m in URL_IN_STRING.finditer(js):
            self._add(base_line + js.count("\n", 0, m.start()), "url in script string", m.group(1))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._attr_check(tag, attrs)
        if tag in ("script", "style"):
            self._in = tag
            self._block_start = self.getpos()[0]
            self._block = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._attr_check(tag.lower(), attrs)

    def handle_endtag(self, tag: str) -> None:
        if self._in and tag.lower() == self._in:
            body = "".join(self._block)
            if self._in == "script":
                self._scan_js(body, self._block_start)
            else:
                self._scan_css(body, self._block_start)
            self._in = None
            self._block = []

    def handle_data(self, data: str) -> None:
        if self._in:
            self._block.append(data)

    def close(self) -> None:  # unterminated <script>/<style> at end of file
        super().close()
        if self._in:
            self.handle_endtag(self._in)


def scan_html(path: Path) -> list[Problem]:
    """Return every off-machine reference found in one page."""
    text = path.read_text(encoding="utf-8", errors="replace")
    s = _Scanner()
    s.feed(text)
    s.close()
    return sorted(s.problems)


def index_names(index_text: str) -> set[str]:
    return set(INDEX_CODE.findall(index_text)) | set(INDEX_LINK.findall(index_text))


def list_items(made: Path) -> list[str]:
    """Files under made/ except README.md, as posix paths relative to made/.

    Only path parts *inside* made/ are tested for a leading dot, so a checkout
    that lives under a hidden directory (e.g. /tmp/.work) is still scanned.
    """
    return sorted(
        p.relative_to(made).as_posix()
        for p in made.rglob("*")
        if p.is_file()
        and p.name != "README.md"
        and not any(part.startswith(".") for part in p.relative_to(made).parts)
    )


def check(root: Path) -> int:
    made = root / "made"
    readme = made / "README.md"
    if not made.is_dir():
        print(f"no made/ directory under {root}")
        return 1

    items = list_items(made)
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
