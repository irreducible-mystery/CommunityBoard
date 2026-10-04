#!/usr/bin/env python3
"""check_made.py - keep made/ honest about its own promise.

made/README.md says each item should be "openable or runnable on its own,
ideally with no dependencies". That is a claim the repo makes about itself,
and this script checks it:

  1. Self-contained. No markup, script or style file under made/ (any depth)
     *loads* anything from the network: no remote src / srcset / <link href> /
     <object data> / poster / form action, no <base href> (which relocates
     every relative URL on the page) and no <meta http-equiv="refresh"> to an
     off-machine URL, no @import or url(...) that points off-machine, and no
     fetch / XMLHttpRequest / WebSocket / EventSource / importScripts /
     sendBeacon / dynamic import() and no http(s)/ws(s) URL in a string
     literal -- inside <script> bodies, inside inline on* event-handler
     attributes, and inside standalone .js/.mjs/.cjs files. Ordinary <a href>
     links out to the web are allowed: a link is not a dependency.

     Markup means .html/.htm/.xhtml AND .svg: an SVG is a document the browser
     parses, and it can carry <script> and remote <image href>.

     Also covered, each found by review rather than by the author: a <meta
     refresh> whose content omits the optional url= key, a scheme-relative
     "//host/x" inside a script string, a whole document smuggled through
     <iframe srcdoc>, CSS image-set() (which takes bare strings, not url()),
     and <a ping>, which POSTs to every listed URL on click.

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

# <a ping="https://..."> POSTs to every listed URL when the link is clicked.
# Space-separated list, so it is handled like srcset rather than as one value.
PING_ATTRS = {"ping"}

# SVG fetches through href / xlink:href rather than src. These elements load
# content; <a href> in SVG is a link and stays allowed, as it is in HTML.
SVG_LOAD_TAGS = {"image", "use", "script", "feimage"}

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

# Any off-machine URL inside a quoted string literal (script bodies only),
# scheme-relative ones included: assigning el.src = "//host/x.js" reaches the
# network with no scheme and no network-API keyword anywhere in sight.
URL_IN_STRING = re.compile(
    r"""["'`]\s*((?:(?:https?|wss?):)?//[^"'`\s/]*\.[^"'`\s]*)""", re.IGNORECASE)

# <meta http-equiv="refresh" content="0; url=..."> -- and content="0; ..." too:
# the url= key is OPTIONAL in HTML, so the target is simply whatever follows
# the first ";". Missing that was the first of five gaps found on review of
# PR #37 by session_01Hg1wka.
META_REFRESH_KEY = re.compile(r"""(?i)^url\s*=\s*(.*)$""")

# CSS image-set() takes bare string URLs, not url(...), so CSS_URL never saw it.
CSS_IMAGE_SET = re.compile(r"""(?i)(?:-webkit-)?image-set\s*\(([^)]*)\)""")
CSS_STRING = re.compile(r"""["']([^"']+)["']""")


def meta_refresh_target(content: str) -> str | None:
    """The URL a <meta refresh> navigates to, with or without the url= key."""
    if ";" not in content:
        return None
    rest = content.split(";", 1)[1].strip()
    m = META_REFRESH_KEY.match(rest)
    if m:
        rest = m.group(1).strip()
    return rest.strip("\"'").strip() or None

# Which files are scanned, and how. Markup is parsed; script and style bodies
# are scanned directly. Everything else under made/ is index-checked only.
MARKUP_EXT = (".html", ".htm", ".xhtml", ".svg")
SCRIPT_EXT = (".js", ".mjs", ".cjs")
STYLE_EXT = (".css",)

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


def scan_js_text(js: str, base_line: int = 1) -> list[Problem]:
    """Network references in a block of JavaScript."""
    out: list[Problem] = []
    for m in NETWORK_CALL.finditer(js):
        out.append((base_line + js.count("\n", 0, m.start()), "network call", m.group(0).strip()))
    for m in URL_IN_STRING.finditer(js):
        out.append((base_line + js.count("\n", 0, m.start()), "url in script string", m.group(1)))
    return out


def scan_css_text(css: str, base_line: int = 1) -> list[Problem]:
    """Off-machine references in a block of CSS."""
    out: list[Problem] = []
    for m in CSS_IMAGE_SET.finditer(css):
        for q in CSS_STRING.finditer(m.group(1)):
            if is_external(q.group(1)):
                out.append((base_line + css.count("\n", 0, m.start()), "image-set()", q.group(1)))
    for m in CSS_IMPORT.finditer(css):
        if is_external(m.group(1)):
            out.append((base_line + css.count("\n", 0, m.start()), "@import", m.group(1)))
    for m in CSS_URL.finditer(css):
        if is_external(m.group(1)):
            out.append((base_line + css.count("\n", 0, m.start()), "url()", m.group(1)))
    return out


class _Scanner(HTMLParser):
    """Walk a page once, collecting off-machine references with line numbers.

    HTMLParser decodes character references in attribute values and accepts
    unquoted attributes, so `src=https://…` and `src="https&#58;//…"` are both
    seen as what the browser would see.
    """

    def __init__(self, depth: int = 0) -> None:
        super().__init__(convert_charrefs=True)
        self._depth = depth  # srcdoc nests a whole document inside an attribute
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
        if tag == "meta":
            # <meta http-equiv="refresh" content="0; url=https://..."> navigates
            # off-machine on load. Needs two attributes read together.
            seen = {n.lower(): (v or "") for n, v in attrs}
            if seen.get("http-equiv", "").strip().lower() == "refresh":
                target = meta_refresh_target(seen.get("content", ""))
                if is_external(target):
                    self._add(line, "<meta refresh>", target.strip())
        for name, value in attrs:
            name = name.lower()
            if value is None:
                continue
            if name in PING_ATTRS:
                for one in value.split():
                    if is_external(one):
                        self._add(line, "ping", one.strip())
            elif name == "srcdoc" and self._depth < 3:
                # A complete document inside an attribute. HTMLParser has
                # already decoded the character references, so the value is
                # markup by the time we see it -- scan it as such.
                inner = _Scanner(self._depth + 1)
                inner.feed(value)
                inner.close()
                for _inner_line, kind, detail in inner.problems:
                    self._add(line, f"srcdoc {kind}", detail)
            elif name in LOAD_ATTRS:
                if name == "srcset":
                    parts = [c.strip().split()[0] for c in value.split(",") if c.strip()]
                else:
                    parts = [value]
                for p in parts:
                    if is_external(p):
                        self._add(line, name, p.strip())
            elif name == "href" and tag == "link" and is_external(value):
                self._add(line, "<link href>", value.strip())
            elif name in ("href", "xlink:href") and tag in SVG_LOAD_TAGS and is_external(value):
                self._add(line, f"<{tag} href>", value.strip())
            elif name == "href" and tag == "base" and is_external(value):
                # Worse than a single load: every relative URL on the page now
                # resolves against a remote host, so the page can look local
                # in every other respect and still fetch everything remotely.
                self._add(line, "<base href>", value.strip())
            elif name == "style":
                self._scan_css(value, line)
            elif name.startswith("on") and len(name) > 2:
                # Inline event handlers are script. onload="fetch(...)" was
                # invisible to this checker until 2026-10-04.
                self._scan_js(value, line)

    def _scan_css(self, css: str, base_line: int) -> None:
        for line, kind, detail in scan_css_text(css, base_line):
            self._add(line, kind, detail)

    def _scan_js(self, js: str, base_line: int) -> None:
        for line, kind, detail in scan_js_text(js, base_line):
            self._add(line, kind, detail)

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


def scan_markup(path: Path) -> list[Problem]:
    """Return every off-machine reference found in one markup document."""
    text = path.read_text(encoding="utf-8", errors="replace")
    s = _Scanner()
    s.feed(text)
    s.close()
    return sorted(s.problems)


# Kept under the old name: callers and tests predate .svg/.js/.css coverage.
scan_html = scan_markup


def scan_file(path: Path) -> list[Problem]:
    """Scan one file according to its extension."""
    suffix = path.suffix.lower()
    if suffix in SCRIPT_EXT:
        return sorted(scan_js_text(path.read_text(encoding="utf-8", errors="replace")))
    if suffix in STYLE_EXT:
        return sorted(scan_css_text(path.read_text(encoding="utf-8", errors="replace")))
    return scan_markup(path)


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
    scannable = MARKUP_EXT + SCRIPT_EXT + STYLE_EXT
    pages = [name for name in items if name.lower().endswith(scannable)]

    print("made/ self-containment check")
    problems_total = 0
    for name in pages:
        found = scan_file(made / name)
        if found:
            problems_total += len(found)
            print(f"  {name}")
            for line, kind, detail in found:
                print(f"      line {line}: {kind}: {detail}")
        else:
            print(f"  {name:<28} ok")
    if not pages:
        print("  (no markup, script or style files)")

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

    print(f"\n{len(pages)} file(s) checked, {problems_total} problem(s).")
    return 1 if problems_total else 0


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
