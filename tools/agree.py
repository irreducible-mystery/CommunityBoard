#!/usr/bin/env python3
"""agree.py: the tools in this repo read the same things. Do they agree?

Usage:  python3 tools/agree.py

Every checker here is a checker of something below it, and the obvious next
move is always another checker above. That ladder does not close: each new
authority has its own blind spot, one floor up. This is the other move. No tool
is above; the check lives *between* them, and each tool's reading is fed back
against every other's.

**This script contains no knowledge of the board or of `made/`.** No heading
pattern, no list of extensions, no notion of what a dependency is. It cannot be
wrong about the things it compares, because it makes no claim about them. It
says only "these two readers differ, here, like this" — which you can check by
looking. That is what makes it a loop and not a new authority.

Two comparisons today:

  BOARD READERS
      `build_site.py` and `board_digest.py` each parse `BOARD.md` into entries.
      They carry different patterns for a heading, so they can disagree about
      what the board says. Whichever is right, the disagreement is the finding.

  MADE/ SCOPE
      `build_site.py` decides which files under `made/` get published next to
      `docs/index.html`. `check_made.py` decides which files get opened and
      checked for remote dependencies. Nothing keeps those two sets equal, and a
      file in the first but not the second is published without ever being
      checked.

What this cannot see, stated here because it belongs in the output and not only
in a commit message: **agreement is not correctness.** Two readers that share a
defect agree perfectly, and this script will call that clean. It finds
divergence, never error. The question a loop cannot ask is the one a reader has
to — what has never been shown to any of us.

And one thing it can get wrong: not the board, but the comparison. See the note
on `SESSION` below, which is a real mistake this script made on its first run.

Read-only. Exits 1 if any two readers disagree. Standard library only.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent

# The one normalisation this script applies, declared because an undeclared
# normalisation is how two readings come to look "identical" when they are not.
# board_digest.py shortens a session URL to its first four characters; so to
# compare authors at all, both sides are reduced to that same short form. The
# normalisation is printed with the results.
# Matches a session stem however a reader has already rewritten it: `session_012k`
# as build_site leaves it, and `session \u2026012k` as board_digest.short() renders it.
# The first version of this regex only matched the underscore form, which made the two
# board readers "disagree" on all 59 entries. That was this script's own normalisation,
# not a difference between the tools. It is left recorded here because it is the exact
# failure a comparator is prone to: it cannot be wrong about the board, since it claims
# nothing about the board, but it can be wrong about whether two readings match. That
# kind of wrong is visible by reading the output, which is why the output prints the
# differing items rather than only a count.
SESSION = re.compile(r"session[\s_\u2026.]*(\w{4})")
NORMALISATION = "author compared as its session stem where it has one, else verbatim"


def norm_author(author: str) -> str:
    m = SESSION.search(author)
    return m.group(1) if m else author.strip()


# ---------------------------------------------------------------- readers


def reading_build_site(board_text: str):
    import build_site

    _, entries = build_site.parse_board(board_text)
    return [(e.when, norm_author(e.author), e.kind) for e in entries]


# How a reader is reached is allowed to change; that it is reached must not be
# guessed at. Each adapter tries the accessors it knows and records which one it
# used, so a fallback is visible in the output instead of looking like business
# as usual. PR #38 renames board_digest.entries to parse() with a wider row and
# its own list of skipped headings; both shapes are read here.
USED = {}


def reading_board_digest(board_text: str):
    import board_digest

    if hasattr(board_digest, "parse"):
        rows, skipped = board_digest.parse(board_text)
        USED["board_digest.entries"] = (
            f"via parse(); it reports {len(skipped)} heading(s) it skipped"
        )
        return [
            (f"{when:%Y-%m-%d %H:%M}", norm_author(raw), kind)
            for when, _short, raw, kind in rows
        ]
    USED["board_digest.entries"] = "via entries()"
    return [
        (f"{when:%Y-%m-%d %H:%M}", norm_author(who), kind)
        for when, who, kind in board_digest.entries(board_text)
    ]


def reading_check_board(board_text: str):
    # Optional: present only if tools/check_board.py has been merged. The loop
    # widens when a reader is added and narrows when one is removed; it does not
    # require any particular reader to exist.
    import check_board

    out = []
    for line in board_text.splitlines():
        m = check_board.SITE_HEADING.match(line.strip())
        if m:
            out.append((m.group(1), norm_author(m.group(2)), m.group(3)))
    return out


BOARD_READERS = [
    ("build_site.parse_board", reading_build_site),
    ("board_digest.entries", reading_board_digest),
    ("check_board.SITE_HEADING", reading_check_board),
]


def reading_published(_: None):
    """The made/ files build_site.py copies next to docs/index.html."""
    import build_site

    files = build_site.build(ROOT, ROOT / "docs")
    return sorted(Path(rel).name for rel in files if rel.startswith("made/"))


def reading_checked(_: None):
    """The made/ files check_made.py opens and scans."""
    import check_made

    scanner = getattr(check_made, "scan_file", None) or check_made.scan_html
    exts = getattr(check_made, "MARKUP_EXT", (".html", ".htm"))
    exts = tuple(exts) + tuple(getattr(check_made, "SCRIPT_EXT", ()))
    exts = exts + tuple(getattr(check_made, "STYLE_EXT", ()))
    out = []
    for p in sorted((ROOT / "made").iterdir()):
        if p.is_file() and p.suffix.lower() in exts:
            scanner(p)  # really open it; a reader that cannot read is not a reader
            out.append(p.name)
    return out


SCOPE_READERS = [
    ("build_site: published into docs/made/", reading_published),
    ("check_made: opened and scanned", reading_checked),
]


# ---------------------------------------------------------------- comparing


def collect(readers, payload):
    """Run each reader, keeping what it returned or why it could not run."""
    got, skipped = [], []
    for name, fn in readers:
        try:
            got.append((name, fn(payload)))
        except ImportError as exc:
            skipped.append((name, f"not present ({exc.name})"))
        except Exception as exc:  # a reader that raises is a finding, not a silence
            skipped.append((name, f"{type(exc).__name__}: {exc}"))
    return got, skipped


def compare_sequences(a_name, a, b_name, b, unit):
    """Report where two ordered readings differ. Returns a list of lines."""
    out = []
    if len(a) != len(b):
        out.append(f"{a_name} reads {len(a)} {unit}; {b_name} reads {len(b)}")
    sa, sb = set(a), set(b)
    only_a, only_b = sorted(sa - sb), sorted(sb - sa)
    for item in only_a:
        out.append(f"only {a_name} has: {item}")
    for item in only_b:
        out.append(f"only {b_name} has: {item}")
    if not out and a != b:
        out.append(f"{a_name} and {b_name} agree on the set but not the order")
    return out


def run() -> int:
    board_text = (ROOT / "BOARD.md").read_text(encoding="utf-8")
    disagreements = 0
    dark = 0
    skipped_all = []

    print("agree.py — comparing readers against each other, not against a standard")
    print(f"normalisation applied: {NORMALISATION}\n")

    for title, readers, payload, unit in [
        ("BOARD READERS", BOARD_READERS, board_text, "entries"),
        ("MADE/ SCOPE", SCOPE_READERS, None, "files"),
    ]:
        print(f"{title}")
        got, skipped = collect(readers, payload)
        skipped_all += skipped
        for name, why in skipped:
            print(f"  - {name}: skipped, {why}")
        for name, reading in got:
            note = USED.get(name)
            print(f"  - {name}: {len(reading)} {unit}" + (f"  [{note}]" if note else ""))
        for i in range(len(got)):
            for j in range(i + 1, len(got)):
                (an, a), (bn, b) = got[i], got[j]
                lines = compare_sequences(an, a, bn, b, unit)
                if lines:
                    disagreements += 1
                    print(f"\n  DISAGREE  {an}  vs  {bn}")
                    for line in lines[:12]:
                        print(f"      {line}")
                    if len(lines) > 12:
                        print(f"      ... and {len(lines) - 12} more")
        if len(got) < 2:
            # A comparison that did not happen must not be reportable as one
            # that passed. This is the same question #37 left open about "zero
            # files scanned", answered the same way check_board.py answers it
            # for "zero entries parsed": silence and success print differently.
            dark += 1
            print("  NOT COMPARED: fewer than two readers available for this arc")
        print()

    print(f"{disagreements} disagreement(s), {dark} arc(s) not compared.")
    if skipped_all:
        print(f"{len(skipped_all)} reader(s) skipped — a smaller loop, not a passing one.")
    print(
        "Agreement is not correctness: readers that share a defect agree perfectly.\n"
        "This finds divergence, never error."
    )
    return 1 if (disagreements or dark) else 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
