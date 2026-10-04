#!/usr/bin/env python3
"""check_stamps.py: compare each BOARD.md heading time with when git says it was written.

Usage:  python3 tools/check_stamps.py [--rev REV] [--tolerance MIN] [--late MIN] [--strict]

`check_board.py` notes entries stamped ahead of the clock, but that check decays: an entry
stamped 40 minutes in the future stops looking wrong 40 minutes later. This one does not
decay. For every `### YYYY-MM-DD HH:MM UTC` heading it asks `git blame` which commit added
that line, and compares the heading with the commit's author time:

- **ahead**: the heading claims a time later than the commit that added it, by more than
  the tolerance (default 2 minutes). An entry cannot be written after it was committed, so
  the stamp is wrong, permanently and checkably.
- **late**: the heading is more than `--late` minutes (default 60) earlier than its commit.
  Usually an entry drafted long before it was pushed; worth knowing, rarely wrong.

Read-only. Exits 0 unless --strict is given and something is ahead. The record is not
rewritten either way: a wrong stamp is corrected by a later entry, not by editing this one.
Standard library and git only.
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HEADING = re.compile(r"^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\b(.*)$")


def blame(repo: Path, rev: str, path: str = "BOARD.md"):
    """Yield (line_number, text, author_time) for every line of path at rev."""
    out = subprocess.run(
        ["git", "-C", str(repo), "blame", "--line-porcelain", rev, "--", path],
        check=True, capture_output=True, text=True,
    ).stdout
    author_time = None
    final_line = None
    for raw in out.splitlines():
        if raw.startswith("\t"):
            yield final_line, raw[1:], author_time
            continue
        parts = raw.split(" ")
        if len(parts[0]) == 40 and len(parts) >= 3 and parts[1].isdigit():
            final_line = int(parts[2])
        elif parts[0] == "author-time":
            author_time = datetime.fromtimestamp(int(parts[1]), tz=timezone.utc)


def check(lines, tolerance=timedelta(minutes=2), late=timedelta(minutes=60)):
    """Return (entries, ahead, late_entries); each finding is (line, heading, stamp, committed)."""
    entries, ahead, behind = 0, [], []
    for number, text, committed in lines:
        m = HEADING.match(text)
        if not m:
            continue
        try:
            stamp = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue  # an impossible date is check_board's business, not this tool's
        entries += 1
        finding = (number, text.strip(), stamp, committed)
        if stamp - committed > tolerance:
            ahead.append(finding)
        elif committed - stamp > late:
            behind.append(finding)
    return entries, ahead, behind


def minutes(delta: timedelta) -> int:
    return round(delta.total_seconds() / 60)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rev", default="HEAD", help="revision to read BOARD.md from (default HEAD; try origin/main)")
    parser.add_argument("--tolerance", type=int, default=2, help="minutes a stamp may run ahead of its commit")
    parser.add_argument("--late", type=int, default=60, help="minutes behind its commit before a stamp is noted")
    parser.add_argument("--strict", action="store_true", help="exit 1 if any entry is stamped ahead of its commit")
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    entries, ahead, behind = check(
        blame(repo, args.rev),
        tolerance=timedelta(minutes=args.tolerance),
        late=timedelta(minutes=args.late),
    )
    print(f"{entries} entries in BOARD.md at {args.rev}, each compared with the commit that added it")
    if not ahead:
        print(f"ahead of their commit: none (tolerance {args.tolerance} min)")
    for number, heading, stamp, committed in ahead:
        print(f"ahead  line {number}: stamped {stamp:%H:%M}, committed {committed:%Y-%m-%d %H:%M} UTC "
              f"(+{minutes(stamp - committed)} min)  {heading}")
    for number, heading, stamp, committed in behind:
        print(f"late   line {number}: stamped {stamp:%H:%M}, committed {committed:%Y-%m-%d %H:%M} UTC "
              f"(-{minutes(committed - stamp)} min)  {heading}")
    return 1 if (args.strict and ahead) else 0


if __name__ == "__main__":
    sys.exit(main())
