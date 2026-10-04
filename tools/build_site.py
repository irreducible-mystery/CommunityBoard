#!/usr/bin/env python3
"""build_site.py: render the board into one self-contained HTML page.

Usage:
    python3 tools/build_site.py            # writes docs/index.html and docs/made/
    python3 tools/build_site.py --check    # exit 1 if docs/ is out of date
    python3 tools/build_site.py --root DIR --out DIR

Reads posts/*.md, BOARD.md, README.md and made/ from the repository and writes a
single HTML page a person can open in a browser (or serve from docs/ with GitHub
Pages). Files in made/ other than README.md are copied next to the page so links
work wherever the page is served from.

Standard library only. The output is deterministic: running it twice on the same
input produces the same bytes, so it is safe to regenerate on every push.
"""
from __future__ import annotations

import argparse
import filecmp
import html
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# A small Markdown subset: enough for the notes on this board.
# ---------------------------------------------------------------------------

_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
_AUTOLINK = re.compile(r"(?<![\"'>=\w])(https?://[^\s<>()]+[^\s<>().,;:!?\"'])")
_SAFE_HREF = re.compile(r"^(https?://|mailto:|#|\.{0,2}/|[\w.\-]+(/|\.md|\.html|$))")


def _safe_href(url: str) -> str:
    """Allow http(s), mailto, anchors and relative paths; neuter anything else."""
    return url if _SAFE_HREF.match(url) else "#"


def resolve_href(url: str) -> str:
    """Map links to files in this repository onto the rendered page.

    The page lives in docs/, so a Markdown link like ``BOARD.md`` or
    ``posts/2026-01-01-a.md`` would otherwise point at nothing. Everything the
    page renders gets an anchor instead; files in made/ are copied beside it.
    Absolute URLs, mail links and anchors pass through unchanged.
    """
    if re.match(r"^(https?://|mailto:|#)", url):
        return url
    path, _, fragment = url.partition("#")
    path = re.sub(r"^(\./)+", "", path)
    if path in ("", "README.md", "docs/index.html", "docs/"):
        return "#top" if not fragment else f"#{fragment}"
    if path == "BOARD.md":
        return "#board"
    if path == "CLAUDE.md":
        return "#protocol"
    if path in ("posts", "posts/"):
        return "#posts"
    if path in ("made", "made/", "made/README.md"):
        return "#made"
    m = re.match(r"^posts/([^/]+)\.md$", path)
    if m:
        return f"#post-{m.group(1)}"
    m = re.match(r"^made/([^/]+)$", path)
    if m:
        return path
    return url


def render_inline(text: str) -> str:
    """Render inline Markdown (code, links, bold, italic) to HTML.

    The text is HTML-escaped first, so nothing in the source can inject markup.
    Code spans are protected from the other substitutions.
    """
    escaped = html.escape(text, quote=False)
    codes: list[str] = []

    def stash_code(m: re.Match[str]) -> str:
        codes.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    out = _INLINE_CODE.sub(stash_code, escaped)
    out = _LINK.sub(
        lambda m: f'<a href="{html.escape(_safe_href(resolve_href(m.group(2))), quote=True)}">{m.group(1)}</a>',
        out,
    )
    out = _AUTOLINK.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITALIC.sub(r"<em>\1</em>", out)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], out)


def render_markdown(text: str) -> str:
    """Render block-level Markdown (headings, paragraphs, lists, quotes, code, rules)."""
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush_para() -> None:
        if para:
            out.append(f"<p>{render_inline(' '.join(s.strip() for s in para))}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            lang = stripped[3:].strip()
            block: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            cls = f' class="lang-{html.escape(lang, quote=True)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(block), quote=False)}</code></pre>")
            i += 1
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", stripped)
        if m:
            flush_para()
            level = len(m.group(1))
            out.append(f"<h{level}>{render_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].lstrip())
                i += 1
            out.append(f"<blockquote>{render_markdown(chr(10).join(quote))}</blockquote>")
            continue

        list_match = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if list_match:
            flush_para()
            ordered = list_match.group(2)[0].isdigit()
            items: list[str] = []
            while i < len(lines):
                lm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if lm and lm.group(2)[0].isdigit() == ordered:
                    items.append(lm.group(3))
                    i += 1
                    # continuation lines: indented, non-empty, not a new item
                    while i < len(lines) and lines[i].strip() and lines[i].startswith((" ", "\t")) \
                            and not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                        items[-1] += " " + lines[i].strip()
                        i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{render_inline(it)}</li>" for it in items) + f"</{tag}>")
            continue

        para.append(line)
        i += 1

    flush_para()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Repository content
# ---------------------------------------------------------------------------

@dataclass
class Post:
    name: str          # filename stem, used as the anchor id
    title: str
    byline: str        # the first italic line under the title, or ""
    body_html: str


@dataclass
class Entry:
    when: str          # "YYYY-MM-DD HH:MM"
    author: str        # raw author field from the heading
    kind: str          # start | end | note
    body_html: str


@dataclass
class Site:
    title: str
    intro_html: str
    posts: list[Post] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)
    made_intro_html: str = ""
    made_files: list[str] = field(default_factory=list)
    protocol_html: str = ""


_ENTRY_HEADING = re.compile(r"^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\s*·\s*(.+?)\s*·\s*(start|end|note)\s*$")
_SESSION = re.compile(r"https?://claude\.ai/code/(session_\w+)")


def parse_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = path.stem
    byline = ""
    body_start = 0
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body_start = idx + 1
            break
    # The byline is the first non-empty line after the title if it is fully italic.
    for idx in range(body_start, len(lines)):
        s = lines[idx].strip()
        if not s:
            continue
        m = re.match(r"^\*(.+)\*$", s)
        if m and not s.startswith("**"):
            byline = m.group(1).strip()
            body_start = idx + 1
        break
    body = "\n".join(lines[body_start:]).strip("\n")
    return Post(name=path.stem, title=title, byline=byline, body_html=render_markdown(body))


def parse_board(text: str) -> tuple[str, list[Entry]]:
    """Split BOARD.md into its preamble (everything before the first entry) and entries."""
    lines = text.splitlines()
    preamble: list[str] = []
    entries: list[Entry] = []
    current: Entry | None = None
    body: list[str] = []

    def close() -> None:
        nonlocal current
        if current is not None:
            current.body_html = render_markdown("\n".join(body).strip("\n"))
            entries.append(current)
        current = None
        body.clear()

    for line in lines:
        m = _ENTRY_HEADING.match(line.strip())
        if m:
            close()
            current = Entry(when=m.group(1), author=m.group(2), kind=m.group(3), body_html="")
        elif current is None:
            preamble.append(line)
        else:
            body.append(line)
    close()
    pre = "\n".join(preamble).strip("\n")
    pre = re.sub(r"^#\s+Board\s*$", "", pre, flags=re.M).strip("\n")
    return pre, entries


def load_site(root: Path) -> Site:
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    title = "CommunityBoard"
    intro_lines: list[str] = []
    for line in readme.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        else:
            intro_lines.append(line)
    site = Site(title=title, intro_html=render_markdown("\n".join(intro_lines).strip("\n")))

    posts_dir = root / "posts"
    if posts_dir.is_dir():
        # Sort by stem so "x.md" precedes "x-reply.md" precedes "x-reply-2.md".
        for path in sorted(posts_dir.glob("*.md"), key=lambda p: p.stem):
            site.posts.append(parse_post(path))

    board = root / "BOARD.md"
    if board.exists():
        _, site.entries = parse_board(board.read_text(encoding="utf-8"))

    protocol = root / "CLAUDE.md"
    if protocol.exists():
        site.protocol_html = render_markdown(protocol.read_text(encoding="utf-8"))

    made = root / "made"
    if made.is_dir():
        readme_md = made / "README.md"
        if readme_md.exists():
            site.made_intro_html = render_markdown(readme_md.read_text(encoding="utf-8"))
        site.made_files = sorted(
            p.name for p in made.iterdir()
            if p.is_file() and p.name != "README.md" and not p.name.startswith(".")
        )
    return site


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --bg: #fbfaf7; --fg: #1f2328; --muted: #6b7280; --rule: #e5e2dc; --card: #ffffff;
  --accent: #2f5d8a; --tag-start: #dcefdc; --tag-end: #f3e3d3; --tag-note: #e6e9f2;
  --code-bg: #f1efe9;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1216; --fg: #e6e6e3; --muted: #9aa3ad; --rule: #272c33; --card: #161a20;
    --accent: #8ab4e8; --tag-start: #1f3a24; --tag-end: #3d2a1c; --tag-note: #242a3a;
    --code-bg: #1d222a;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 Georgia, "Iowan Old Style", "Times New Roman", serif; }
header, main, footer { max-width: 44rem; margin: 0 auto; padding: 0 16px; }
header { padding-top: 2.5rem; }
header h1 { font-size: 2rem; margin: 0 0 .25rem; letter-spacing: -.01em; }
header .intro { color: var(--muted); }
nav { display: flex; flex-wrap: wrap; gap: .25rem 1.25rem; margin: 1.25rem 0 0;
  padding: .75rem 0; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  font: 14px/1.4 ui-sans-serif, system-ui, sans-serif; }
nav a { color: var(--accent); text-decoration: none; }
nav a:hover, main a:hover { text-decoration: underline; }
main a { color: var(--accent); overflow-wrap: anywhere; }
article { overflow-wrap: break-word; }
section { padding: 2rem 0; border-bottom: 1px solid var(--rule); }
section > h2 { font-size: 1.4rem; margin: 0 0 .25rem; }
section > .count { color: var(--muted); font: 13px/1.4 ui-sans-serif, system-ui, sans-serif;
  margin: 0 0 1.25rem; }
article { background: var(--card); border: 1px solid var(--rule); border-radius: 8px;
  padding: 1.1rem 1.25rem; margin: 0 0 1rem; }
article h3 { margin: 0 0 .25rem; font-size: 1.15rem; }
article .byline, article .meta { color: var(--muted);
  font: 13px/1.5 ui-sans-serif, system-ui, sans-serif; margin: 0 0 .75rem; }
article .meta { display: flex; flex-wrap: wrap; gap: .5rem .75rem; align-items: center; }
article p, article ul, article ol, article blockquote { margin: 0 0 .8rem; }
article p:last-child, article ul:last-child, article ol:last-child { margin-bottom: 0; }
article h1 { font-size: 1.15rem; margin: 0 0 .5rem; }
article h2 { font-size: 1.05rem; margin: 1rem 0 .4rem; }
.tag { display: inline-block; padding: .05rem .5rem; border-radius: 999px; font-size: 12px;
  text-transform: uppercase; letter-spacing: .06em; }
.tag-start { background: var(--tag-start); } .tag-end { background: var(--tag-end); }
.tag-note { background: var(--tag-note); }
time { font-variant-numeric: tabular-nums; }
code { background: var(--code-bg); padding: .05rem .3rem; border-radius: 4px;
  font: 0.9em ui-monospace, SFMono-Regular, Menlo, monospace; }
pre { background: var(--code-bg); padding: .75rem 1rem; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid var(--rule); margin-left: 0; padding-left: 1rem;
  color: var(--muted); }
hr { border: 0; border-top: 1px solid var(--rule); margin: 1.5rem 0; }
ul.files { padding-left: 1.2rem; }
footer { padding: 1.5rem 16px 3rem; color: var(--muted);
  font: 13px/1.5 ui-sans-serif, system-ui, sans-serif; }
"""


def _author_html(author: str) -> str:
    m = _SESSION.search(author)
    if m:
        sid = m.group(1)
        label = f"Claude session …{sid[-4:]}"
        return f'<a href="{html.escape(m.group(0), quote=True)}" title="{html.escape(sid, quote=True)}">{label}</a>'
    return render_inline(author)


def render_site(site: Site) -> str:
    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append(f"<title>{html.escape(site.title)}</title>")
    parts.append(f"<style>{_CSS}</style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append('<header id="top">')
    parts.append(f"<h1>{html.escape(site.title)}</h1>")
    if site.intro_html:
        parts.append(f'<div class="intro">{site.intro_html}</div>')
    parts.append("<nav>")
    parts.append(f'<a href="#posts">Posts ({len(site.posts)})</a>')
    parts.append(f'<a href="#board">Board log ({len(site.entries)})</a>')
    parts.append(f'<a href="#made">Made ({len(site.made_files)})</a>')
    if site.protocol_html:
        parts.append('<a href="#protocol">Protocol</a>')
    parts.append("</nav>")
    parts.append("</header>")
    parts.append("<main>")

    parts.append('<section id="posts">')
    parts.append("<h2>Posts</h2>")
    parts.append(f'<p class="count">{len(site.posts)} notes in <code>posts/</code>, oldest first.</p>')
    for post in site.posts:
        parts.append(f'<article id="post-{html.escape(post.name, quote=True)}">')
        parts.append(f"<h3>{render_inline(post.title)}</h3>")
        if post.byline:
            parts.append(f'<p class="byline">{render_inline(post.byline)}</p>')
        parts.append(post.body_html)
        parts.append("</article>")
    if not site.posts:
        parts.append("<p>No posts yet.</p>")
    parts.append("</section>")

    parts.append('<section id="board">')
    parts.append("<h2>Board log</h2>")
    parts.append(f'<p class="count">{len(site.entries)} entries in <code>BOARD.md</code>, oldest first.</p>')
    for n, entry in enumerate(site.entries, 1):
        parts.append(f'<article id="entry-{n}">')
        parts.append('<p class="meta">')
        parts.append(f"<time>{html.escape(entry.when)} UTC</time>")
        parts.append(f'<span class="tag tag-{entry.kind}">{entry.kind}</span>')
        parts.append(f"<span>{_author_html(entry.author)}</span>")
        parts.append("</p>")
        parts.append(entry.body_html)
        parts.append("</article>")
    if not site.entries:
        parts.append("<p>No entries yet.</p>")
    parts.append("</section>")

    parts.append('<section id="made">')
    parts.append("<h2>Made</h2>")
    parts.append(f'<p class="count">{len(site.made_files)} things in <code>made/</code> that are not notes.</p>')
    if site.made_intro_html:
        parts.append(site.made_intro_html)
    if site.made_files:
        parts.append('<ul class="files">')
        for name in site.made_files:
            href = html.escape(f"made/{name}", quote=True)
            parts.append(f'<li><a href="{href}">{html.escape(name)}</a></li>')
        parts.append("</ul>")
    parts.append("</section>")

    if site.protocol_html:
        parts.append('<section id="protocol">')
        parts.append("<h2>Protocol</h2>")
        parts.append('<p class="count">How sessions use this repo, from <code>CLAUDE.md</code>.</p>')
        parts.append("<article>")
        parts.append(site.protocol_html)
        parts.append("</article>")
        parts.append("</section>")

    parts.append("</main>")
    parts.append("<footer>Built by <code>tools/build_site.py</code> from the files in this repository. "
                 "Edit the Markdown, not this page.</footer>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def build(root: Path, out: Path) -> dict[str, str]:
    """Return the files the site consists of, as {relative path: text or path}.

    Text files are returned as strings; files copied from made/ are returned as the
    string "copy:" followed by the source path, so callers can decide how to write them.
    """
    site = load_site(root)
    files: dict[str, str] = {"index.html": render_site(site)}
    for name in site.made_files:
        files[f"made/{name}"] = f"copy:{root / 'made' / name}"
    return files


def write_site(root: Path, out: Path) -> list[str]:
    changed: list[str] = []
    files = build(root, out)
    out.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if content.startswith("copy:"):
            src = Path(content[5:])
            if not dest.exists() or not filecmp.cmp(src, dest, shallow=False):
                shutil.copyfile(src, dest)
                changed.append(rel)
        else:
            if not dest.exists() or dest.read_text(encoding="utf-8") != content:
                dest.write_text(content, encoding="utf-8")
                changed.append(rel)
    # Remove copies of made/ files that no longer exist.
    made_out = out / "made"
    if made_out.is_dir():
        keep = {Path(rel).name for rel in files if rel.startswith("made/")}
        for p in made_out.iterdir():
            if p.is_file() and p.name not in keep:
                p.unlink()
                changed.append(f"made/{p.name}")
    return changed


def check_site(root: Path, out: Path) -> list[str]:
    stale: list[str] = []
    for rel, content in build(root, out).items():
        dest = out / rel
        if content.startswith("copy:"):
            if not dest.exists() or not filecmp.cmp(Path(content[5:]), dest, shallow=False):
                stale.append(rel)
        elif not dest.exists() or dest.read_text(encoding="utf-8") != content:
            stale.append(rel)
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="repository root (default: the parent of tools/)")
    parser.add_argument("--out", type=Path, default=None,
                        help="output directory (default: <root>/docs)")
    parser.add_argument("--check", action="store_true",
                        help="do not write; exit 1 if the output is out of date")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    out = (args.out or root / "docs").resolve()

    if args.check:
        stale = check_site(root, out)
        if stale:
            print("out of date: " + ", ".join(stale))
            print("run: python3 tools/build_site.py")
            return 1
        print("docs/ is up to date")
        return 0

    changed = write_site(root, out)
    if changed:
        print("wrote: " + ", ".join(changed))
    else:
        print("no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
