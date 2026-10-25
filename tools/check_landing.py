#!/usr/bin/env python3
"""check_landing.py: is a repair to the board sitting open while the board stays short?

Usage:
    python3 tools/check_landing.py              # exit 1 if an open PR holds more board
                                                # entries than main does
    python3 tools/check_landing.py --repo .     # another checkout

WHY

On 2026-10-14 PR #208 restored the board entries that had left main. It was read
end to end the same evening and called good. It did not merge. By 2026-10-15 it
was conflicted, and main had taken 21 more commits to BOARD.md; by 2026-10-18,
26 more, with main showing 19 entries against the 442 that #223 (a second
restore, mergeable since 10-17) holds. Nobody decided this. No check could say
it. "Approved" and "merged" were connected by nothing (#221, 2026-10-15).

This is the gap between a repair existing and a repair landing, and it is the
one failure of the record that has been named by two independent sessions and
is still in progress. The check makes it visible without naming a person.

WHAT IT CHECKS, AND WHAT IT REFUSES TO

It counts `### ` headings in BOARD.md on main and on the head of every open pull
request. If any open PR holds more entries than main, the surface is missing
entries that a candidate repair already holds, and that is a failing condition:
the check prints the PR, its age, how many commits main has taken to BOARD.md
since the two diverged, and the command that shows the difference.

It does not read approvals, reviews or comments. Every session and the owner
write here under one login, so the record cannot say who approved what, and a
check that matched the word "approved" in prose would be a semantic check on a
shared account. Entry counts are bytes; they cannot be attributed and do not
need to be.

It does not block anything. It runs after the fact and goes red. The condition
clears when the repair merges or main is made whole another way; it is an
integrity condition, not a timer.

Exit codes:
  0  no open PR holds more board entries than main
  1  at least one does (printed)
  2  could not list the open PRs or read a board: a failed probe, never a pass
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HEADING = "### "


class ProbeFailure(Exception):
    pass


# ---- pure part: tested without git or network -------------------------------------------

def count_entries(text: str) -> int:
    """Board entries are lines beginning '### ' (the convention check_board.py reads)."""
    return sum(1 for line in text.splitlines() if line.startswith(HEADING))


def gaps(main_entries: int, prs: list[dict]) -> list[dict]:
    """The open PRs whose board holds more entries than main's.

    Each PR dict carries at least `number` and `entries`. Returned in order of
    the size of the gap, largest first, so the most complete repair is printed
    first.
    """
    out = [dict(pr, gap=pr["entries"] - main_entries) for pr in prs if pr["entries"] > main_entries]
    return sorted(out, key=lambda p: (-p["gap"], p["number"]))


def report(main_entries: int, found: list[dict], checked: int) -> str:
    if not found:
        return (f"BOARD.md on main holds {main_entries} entries; none of the {checked} open "
                f"pull request(s) holds more.")
    lines = [f"BOARD.md on main holds {main_entries} entries. {len(found)} open pull request(s) hold more:"]
    for p in found:
        age = f", open {p['age_days']} day(s)" if "age_days" in p else ""
        since = (f", main has taken {p['main_commits_since']} commit(s) to BOARD.md since they diverged"
                 if "main_commits_since" in p else "")
        lines.append(f"  #{p['number']}: {p['entries']} entries (+{p['gap']}){age}{since}")
        if "head" in p:
            lines.append(f"      see: git diff --stat origin/main {p['head']} -- BOARD.md")
    lines.append("A repair exists and has not landed. This clears when one merges or main is made whole.")
    return "\n".join(lines)


# ---- probing part: git and gh --------------------------------------------------------------

def run(args: list[str], cwd: Path) -> str:
    try:
        out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ProbeFailure(f"{' '.join(args[:2])} did not run: {e}") from e
    if out.returncode != 0:
        raise ProbeFailure(f"{' '.join(args[:2])} failed: {out.stderr.strip()[:300]}")
    return out.stdout


def open_prs(cwd: Path) -> list[dict]:
    text = run(["gh", "pr", "list", "--state", "open", "--limit", "200",
                "--json", "number,headRefOid,createdAt,isDraft"], cwd)
    try:
        prs = json.loads(text)
    except json.JSONDecodeError as e:
        raise ProbeFailure(f"gh returned something that is not JSON: {e}") from e
    if not isinstance(prs, list):
        raise ProbeFailure("gh returned no list of pull requests")
    return prs


def board_at(rev: str, cwd: Path) -> int | None:
    """Entries in BOARD.md at a revision, or None if that revision has no BOARD.md."""
    out = subprocess.run(["git", "show", f"{rev}:BOARD.md"], cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return count_entries(out.stdout)


def probe(root: Path) -> tuple[int, list[dict], int]:
    run(["git", "fetch", "--quiet", "origin", "main"], root)
    main_entries = board_at("origin/main", root)
    if main_entries is None:
        raise ProbeFailure("origin/main has no BOARD.md")
    prs = open_prs(root)
    if not prs:
        raise ProbeFailure("gh listed zero open pull requests; this repository always has some, "
                           "so the listing failed rather than the gap being closed")
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    for pr in prs:
        head = pr["headRefOid"]
        try:
            run(["git", "fetch", "--quiet", "origin", head], root)
        except ProbeFailure:
            run(["git", "fetch", "--quiet", "origin", f"pull/{pr['number']}/head"], root)
        entries = board_at(head, root)
        if entries is None:
            continue
        row = {"number": pr["number"], "entries": entries, "head": head[:7]}
        try:
            row["age_days"] = (now - datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))).days
        except (KeyError, ValueError):
            pass
        base = subprocess.run(["git", "merge-base", "origin/main", head], cwd=root,
                              capture_output=True, text=True)
        if base.returncode == 0:
            n = subprocess.run(["git", "rev-list", "--count", f"{base.stdout.strip()}..origin/main", "--", "BOARD.md"],
                               cwd=root, capture_output=True, text=True)
            if n.returncode == 0:
                row["main_commits_since"] = int(n.stdout.strip() or 0)
        rows.append(row)
    return main_entries, gaps(main_entries, rows), len(prs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=None, help="repository root (default: the parent of tools/)")
    args = ap.parse_args(argv)
    root = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent
    try:
        main_entries, found, checked = probe(root)
    except ProbeFailure as e:
        print(f"probe failed: {e}")
        print("exit 2: nothing was checked, so this is not a pass.")
        return 2
    print(report(main_entries, found, checked))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
