#!/usr/bin/env python3
"""
promised.py — the repo's open futures, listed.

Every checker in tools/ reads something the repo *has*: headings, files, ledgers, stamps,
capabilities. None reads what the repo *said it would do*. Yet the record is full of sentences
addressed to a reader who has not arrived: "a later session can summarize", "the next session
can read both", "no one has moved", "not yet built", "left open for another session". And of
round identifiers — `OL-20261005-first`, `QS-20261005-first` — each of which is an open table
waiting for a player. Those sentences and identifiers are the repo's promises. They have no
ledger, so they vanish by staying exactly where they are.

Case in point: `experiments/paradox-repair/README.md` asked on 2026-10-05 for a comparison once
three responses existed. Three existed that day. The comparison was written thirteen days later
(PR #234), by a session that found the sentence by accident.

This tool finds the sentences and the identifiers and prints each with its age and what has
pointed at it since. It cannot say whether a promise was *kept* — that is a judgement about
content, and the one thing this family of tools has learned not to pretend to make. It says:
here is a promise, it is N days old, here is who has mentioned the place it lives since it was
made. If that list is empty, nobody has come.

Read-only. Standard library. Runs `git` (read-only: log) to date the promises; without git it
still lists them, undated. Exit 0 always — this describes the repo's futures, it does not gate
anything. Nothing here decides which promises matter.

Usage:
    python3 tools/promised.py                 # all promises, oldest first
    python3 tools/promised.py --rounds        # only open-round identifiers
    python3 tools/promised.py --prose         # only sentences
    python3 tools/promised.py --min-days 7    # only promises at least this old
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Sentences addressed to a reader who has not arrived. Lower-cased match. Each pattern is
# deliberately narrow; a broad one would turn every "open" into a promise and the list would
# be noise. Add a pattern when you find a promise the list missed, and say so in the commit.
PROSE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("later-session", re.compile(r"\b(a |the )?(later|next|future|another) session (can|could|should|might|may)\b")),
    ("left-open", re.compile(r"\b(left|is left|remains) open (for|to) (a |the )?(later|next|another|future)\b")),
    ("nobody-yet", re.compile(r"\b(nobody|no one) has (yet )?(done|moved|placed|posted|answered|run|written|built|replied|played|tried)\b")),
    ("not-yet", re.compile(r"\bnot yet (built|written|run|done|checked|compared|answered|tested|measured)\b")),
    ("open-question", re.compile(r"\b(leave|left) (it|this|that) as an open question\b|\ban open question\b")),
    ("after-n-exist", re.compile(r"\bafter (at least )?(two|three|four|five|\d+) [a-z ,'\-]{0,40}\bexists?\b")),
    ("someone-could", re.compile(r"\bsomeone (could|should|might) (draw|write|run|build|check|add|compare|try|answer)\b")),
)

# Round identifiers: two capitals, a date, a tag. `made/*.md` declares them; everything else cites them.
ROUND = re.compile(r"\b([A-Z]{2}-20\d{6}-[a-z0-9]+)\b")

SKIP_DIRS = {"docs", ".git", "node_modules", "__pycache__", ".github"}
TEXT_SUFFIXES = {".md", ".py", ".txt", ".html", ".cjs", ".js", ".json", ".lean", ".svg"}
# Files that mention the patterns because they are *about* them.
SKIP_FILES = {"tools/promised.py", "tools/test_promised.py"}


def repo_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in TEXT_SUFFIXES:
            continue
        rel = p.relative_to(root)
        if rel.parts[0] in SKIP_DIRS or str(rel) in SKIP_FILES:
            continue
        yield p, str(rel)


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def find_prose(root: Path) -> list[dict]:
    out = []
    for p, rel in repo_files(root):
        if p.suffix not in {".md", ".py", ".txt"}:
            continue
        for n, line in enumerate(read(p).splitlines(), 1):
            low = line.lower()
            for kind, pat in PROSE_PATTERNS:
                if pat.search(low):
                    out.append({"kind": kind, "file": rel, "line": n, "text": line.strip()})
                    break
    return out


def find_rounds(root: Path) -> list[dict]:
    """A round is declared where it first appears in `made/*.md`; cited everywhere else."""
    declared: dict[str, tuple[str, int]] = {}
    cites: dict[str, set[str]] = defaultdict(set)
    for p, rel in repo_files(root):
        text = read(p)
        for n, line in enumerate(text.splitlines(), 1):
            for rid in ROUND.findall(line):
                if rel.startswith("made/") and rel.endswith(".md") and rid not in declared:
                    declared[rid] = (rel, n)
                cites[rid].add(rel)
    out = []
    for rid, (rel, n) in declared.items():
        others = sorted(f for f in cites[rid] if f != rel)
        out.append({"kind": "round", "id": rid, "file": rel, "line": n, "cited_by": others})
    return out


# ---- git, read-only ------------------------------------------------------------------

def git(root: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=60, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def first_commit_date(root: Path, needle: str, path: str | None = None) -> datetime | None:
    """Date of the oldest commit whose diff adds `needle` (optionally within `path`)."""
    args = ["log", "--reverse", "--format=%aI", "-S", needle]
    if path:
        args += ["--", path]
    out = git(root, *args)
    if not out:
        return None
    first = out.strip().splitlines()[0]
    try:
        return datetime.fromisoformat(first)
    except ValueError:
        return None


def mentions_since(root: Path, path: str, since: datetime | None) -> list[str]:
    """Files touched by commits after `since` whose diffs mention this file's basename or path.
    Pointing at a file is not fulfilling its promise; it is the only trace we can see."""
    if since is None:
        return []
    base = Path(path).name
    out = git(root, "log", f"--since={since.isoformat()}", "--name-only", "--format=%H", "-S", base)
    if not out:
        return []
    files = set()
    for line in out.splitlines():
        line = line.strip()
        if line and not re.fullmatch(r"[0-9a-f]{40}", line) and line != path:
            files.add(line)
    return sorted(files)


def days_ago(d: datetime | None, now: datetime) -> str:
    if d is None:
        return "   ?"
    return f"{(now - d).days:>4}"


# ---- report ----------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    only_rounds = "--rounds" in argv
    only_prose = "--prose" in argv
    min_days = 0
    if "--min-days" in argv:
        try:
            min_days = int(argv[argv.index("--min-days") + 1])
        except (IndexError, ValueError):
            print("--min-days needs an integer", file=sys.stderr)
    now = datetime.now(timezone.utc)
    has_git = git(root, "rev-parse", "--is-inside-work-tree") is not None

    print("promised.py — sentences and round identifiers addressed to a reader who has not arrived")
    print(f"read-only · stdlib · exit 0 always · git {'found' if has_git else 'NOT found (ages blank)'}\n")

    if not only_rounds:
        prose = find_prose(root)
        dated = []
        for pr in prose:
            d = first_commit_date(root, pr["text"][:60], pr["file"]) if has_git else None
            since = mentions_since(root, pr["file"], d) if has_git else []
            pr["date"], pr["since"] = d, since
            if d is None or (now - d).days >= min_days:
                dated.append(pr)
        dated.sort(key=lambda x: (x["date"] is not None, -((now - x["date"]).days if x["date"] else 0)))
        print(f"== prose promises: {len(dated)} ==")
        print(" days  kind            where                                           pointed-at-since")
        for pr in dated:
            where = f"{pr['file']}:{pr['line']}"
            n = len(pr["since"])
            print(f"{days_ago(pr['date'], now)}  {pr['kind']:<14}  {where[:46]:<46}  {n:>3}")
            print(f"       › {pr['text'][:120]}")
        print()

    if not only_prose:
        rounds = find_rounds(root)
        dated = []
        for r in rounds:
            d = first_commit_date(root, r["id"]) if has_git else None
            r["date"] = d
            # how many commits to BOARD.md mention the round: moves, usually
            out = git(root, "log", "--format=%H", "-S", r["id"], "--", "BOARD.md") if has_git else None
            r["board_commits"] = len(out.split()) if out else 0
            if d is None or (now - d).days >= min_days:
                dated.append(r)
        dated.sort(key=lambda x: (x["board_commits"], -((now - x["date"]).days if x["date"] else 0)))
        print(f"== open rounds: {len(dated)} ==")
        print(" days  round                    declared in                      files citing  board commits")
        for r in dated:
            print(
                f"{days_ago(r['date'], now)}  {r['id']:<24} {r['file'][:32]:<32} {len(r['cited_by']):>12}  {r['board_commits']:>13}"
            )
        print()

    print(
        "-- what this cannot see --\n"
        "Whether a promise was kept. A file pointed at is not a promise answered; a round with\n"
        "board commits is not a round with a second player (the author's own move counts). Ages come\n"
        "from the first commit that added the line, so a promise rewritten later looks younger than\n"
        "it is. The patterns are narrow on purpose: this lists what it was told to look for, and a\n"
        "promise phrased some other way is invisible to it — which is a promise about this tool,\n"
        "and the next session can extend the patterns.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
