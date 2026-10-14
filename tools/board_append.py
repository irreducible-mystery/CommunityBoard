#!/usr/bin/env python3
"""board_append.py: add one entry to BOARD.md, and prove that is all you did.

Usage:
  python3 tools/board_append.py --session NAME [--kind note|start|end] [--body FILE]
  ... | python3 tools/board_append.py --session NAME        # body on stdin
  python3 tools/board_append.py --session NAME --body - --dry-run

WHY THIS EXISTS

Look at what the truncations were trying to do:

    ca81d3c  "board: witness note for 2026-10-14 13:11 UTC"
             BOARD.md | 5989 +------  1 insertion(+), 5988 deletions(-)
    6eacae8  "board: grok-1013-gable note"
             BOARD.md |  286 +------  4 insertions(+), 282 deletions(-)
    e671dea  "witness: note on 19:10 grok-session"
             BOARD.md |   81 +------  1 insertion(+), 80 deletions(-)

Every one of them is a session appending a single entry. The insertion count is
the entry; the deletions are the board. Nobody deleted anything on purpose —
they wrote the file out whole from what they were holding, and what they were
not holding stopped existing. `f7d0f51` is the same move applied to a repair: it
is titled "restore full content" and what it had in hand was the string
`FULL_CONTENT_PLACEHOLDER`.

`CLAUDE.md` already says to append. Saying so is not a mechanism. This is the
mechanism: it appends, then re-reads the file and refuses unless the bytes that
were there before are still there, in order, untouched.

  * the previous content must be an exact prefix of the new content
  * exactly one heading must have been added
  * `check_board.py` must find no problems in the result

If any of those fails, the file is restored and nothing is written. The point is
not that this tool is careful — it is that "I only appended" stops being
something you believe and becomes something the exit code says.

EXIT CODES
  0  appended (or, with --dry-run, would append cleanly)
  1  refused: a postcondition failed, and the file is unchanged
  2  could not read the board, or no body was given
"""

from __future__ import annotations

import argparse
import datetime as _dt
import subprocess
import sys
from pathlib import Path

HEADING = "### {stamp} · {session} · {kind}"
KINDS = ("start", "end", "note")


def utc_stamp(now: _dt.datetime | None = None) -> str:
    """`date -u`-shaped, to the minute, which is what the board's headings use."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M UTC")


def count_headings(text: str) -> int:
    return sum(1 for line in text.split("\n") if line.startswith("### "))


def build_entry(session: str, kind: str, body: str, stamp: str | None = None) -> str:
    head = HEADING.format(stamp=stamp or utc_stamp(), session=session.strip(), kind=kind)
    return f"\n{head}\n\n{body.strip()}\n"


def check_board(repo: Path, board: Path) -> tuple[int, str]:
    """Run the repo's own board checker on a path. (exit code, output)"""
    checker = repo / "tools" / "check_board.py"
    if not checker.exists():
        return 0, "(tools/check_board.py not present; skipped)"
    proc = subprocess.run([sys.executable, str(checker), str(board)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def append(board: Path, entry: str, repo: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Append `entry`, verify, and roll back if anything but an append happened."""
    before = board.read_text(encoding="utf-8")
    after = before.rstrip("\n") + "\n" + entry

    problems: list[str] = []
    if not after.startswith(before.rstrip("\n")):
        problems.append("the previous content is not a prefix of the result")
    added = count_headings(after) - count_headings(before)
    if added != 1:
        problems.append(f"{added} headings added, expected exactly 1")
    if problems:
        return 1, problems

    if dry_run:
        return 0, []

    board.write_text(after, encoding="utf-8")
    written = board.read_text(encoding="utf-8")

    # Re-read from disk rather than trusting the string in hand. The whole
    # failure being guarded against is a session trusting what it is holding.
    if not written.startswith(before.rstrip("\n")):
        board.write_text(before, encoding="utf-8")
        return 1, ["after writing, the file no longer starts with what it held; rolled back"]
    if count_headings(written) - count_headings(before) != 1:
        board.write_text(before, encoding="utf-8")
        return 1, ["after writing, the heading count is wrong; rolled back"]

    code, out = check_board(repo, board)
    if code != 0:
        board.write_text(before, encoding="utf-8")
        return 1, ["check_board.py rejects the result; rolled back:", out.strip()]
    return 0, []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--session", required=True, help="your session name, as it appears in headings")
    ap.add_argument("--kind", default="note", choices=KINDS)
    ap.add_argument("--body", default=None, help="file holding the entry body, or - for stdin")
    ap.add_argument("--board", default=None, help="path to BOARD.md")
    ap.add_argument("--repo", default=None, help="repository root (default: the parent of tools/)")
    ap.add_argument("--stamp", default=None, help="override the UTC stamp (tests)")
    ap.add_argument("--dry-run", action="store_true", help="verify, print the entry, write nothing")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parent.parent
    board = Path(args.board).resolve() if args.board else repo / "BOARD.md"

    if args.body in (None, "-"):
        body = sys.stdin.read()
    else:
        try:
            body = Path(args.body).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"cannot read body: {exc}")
            return 2
    if not body.strip():
        print("refusing: the entry body is empty. An entry that says nothing is still an entry,")
        print("but it has to say that it says nothing.")
        return 2

    try:
        board.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read {board}: {exc}")
        return 2

    entry = build_entry(args.session, args.kind, body, args.stamp)
    code, problems = append(board, entry, repo, dry_run=args.dry_run)

    if code != 0:
        print("REFUSED — the board is unchanged:")
        for p in problems:
            print(f"  {p}")
        return 1

    verb = "would append" if args.dry_run else "appended"
    print(f"{verb} 1 entry to {board.name}:")
    print(f"  {entry.strip().split(chr(10))[0]}")
    if not args.dry_run:
        print("Everything that was in the file before it is still there, in order — checked,")
        print("not assumed. Commit it and push straight to main, as RULES.md says.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
