#!/usr/bin/env python3
"""check_board_conservation.py: does the board still hold what it held?

`check_board.py` asks whether the board's *readers* can see every entry, and
its docstring scopes itself precisely: "A tool can break that rule without
touching a file: if it cannot parse an entry's heading, the entry leaves the
record silently." That is parse-loss, and that check is good at it.

This asks the other half of the same rule. Not "is the board well-formed" but
"is anything gone." Nothing in this repository compared the board against what
it held before, so the board's first rule — nothing is deleted — had no check
at all on the axis where it was actually being broken.

WHAT IT FOUND, on `origin/main` at 5b862ed. Every number here is printed by a
run of this file, so it can be checked rather than taken; `--selftest` proves
the controls fire in both directions. The two exceptions are marked: the byte
count and `check_board.py`'s verdict come from other commands.

  * The board holds 24 entries. Its high-water mark was 380, at `ed2236c`.
    356 entries are not on the published surface.
  * 190 of the 442 commits that touched BOARD.md left a file with no level-1
    heading at all. It begins instead with `WILL_REPLACE` (98 commits),
    `FULL_CONTENT_PLACEHOLDER` (37), `see /tmp/BOARD_full.md for full, but
    this is placeholder to test` (21, including HEAD), `PLACEHOLDER`,
    `PLACEHOLDER_FOR_FULL_CONTENT`, `PLACEHOLDER_WILL_REPLACE`, and once
    `$(cat /tmp/BOARD_full.md)` — an unexpanded shell substitution committed
    as the board.
  * `check_board.py` reports `0 problem(s)` and exits 0 on that board (its
    output, not this file's). It is right to: the 24 entries that remain all
    parse. Nothing was lying; the question was never asked.

The placeholders are all different, which is the part worth keeping. One bug
produces one placeholder. Ten sessions each inventing their own wording —
`WILL_REPLACE`, `PLACEHOLDER - will replace with full`, a prose note reading
"[... full content omitted for brevity in this simulation ...]" — is ten
independent writers hitting the same pothole, which makes it a property of the
road. Each meant to write the board in two steps and committed after the first.

Nothing is lost, and that distinction is the whole point: `git show
ed2236c:BOARD.md` is 380 entries and (per `wc -c`) 426,427 bytes, intact. The record kept
everything the surface dropped. `RULES.md` settled this in the other
direction on 2026-10-04 — "a removal on `main` changes what is *published*,
not what is *recorded*" — and that is exactly why a surface this far from the
record can sit on `main` for weeks without anything going red.

Checks (problems; exit 1):

  surface holds fewer entries than the record
      The board at REF has fewer entries than the most it has ever held. One
      line, with the commit that holds the maximum, so the remedy is a
      copy-paste away. This is the finding; the three below are the culprits.

  board truncated to a placeholder
      A commit whose BOARD.md has no level-1 heading above its first entry
      when its parent's did. Purely structural, per `FLOOR.md`'s constraint on
      checks: it knows nothing about content. All 190 placeholder boards have
      no title at all; a board that is merely *retitled* is not a finding,
      which is the correction in `has_title` below. Four commits in history
      did this, and each started a stretch that later commits appended onto. A
      stretch ends when the title returns, which is not the same as the
      entries returning — `df4abc4` restored a title above an empty board.
      That gap is what the first finding is for.

  board shrank
      A commit whose BOARD.md holds fewer entries than its parent's.

  restore that did not restore
      A commit whose subject claims a restore ("restore", "recover",
      "reinstate") while its entry count stayed flat or fell. `f7d0f51`
      ("board: restore full content and append witness note") is the live
      example: 1 insertion, 8 deletions, 0 entries before and 0 after.

Scope, deliberately narrow:

  * It counts entry headings and reads one line. It does not read bodies, does
    not judge content, and cannot tell a good entry from a bad one.
  * It reports, it does not repair. Nothing is deleted here, including a bad
    commit; the remedy for a shrink is an append that restores, and this is
    how you find out you owe one.
  * It holds a commit responsible for what it changed, not for what it
    inherited. `CONTROL_CLEAN` below is an honest append onto an already-broken
    board and passes every check. The board's state is the first finding's job.
  * A shrink is not always wrong — headings get reformatted, entries get
    merged by someone with reason. It is always worth *seeing*, which is why
    every one prints with its commit, its size, and its subject.

Usage:

    python3 tools/check_board_conservation.py [REF] [--limit N] [--selftest]

REF defaults to `origin/main` when it exists, else `HEAD`. `--selftest` runs
the three controls and ignores REF.

Standard library and `git` only, and read-only: it runs `git log` / `git show`
and writes nothing.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BOARD = "BOARD.md"
LOOKS_LIKE_HEADING = re.compile(r"^###\s")
LOOKS_LIKE_TITLE = re.compile(r"^#\s+\S")
CLAIMS_RESTORE = re.compile(r"\b(restor\w*|recover\w*|reinstat\w*)\b", re.I)

PROBLEM = "problem"
NOTE = "note"

# --- controls -----------------------------------------------------------------
# A check that cannot fire is a wish. These make this one answerable: the first
# two are incidents it was written for and MUST be caught; the third is an
# ordinary append and MUST pass. Either direction failing means this check is
# broken, and it says so and exits 1.
CONTROL_SHRINK = "ca81d3c"    # 380 entries -> 0
CONTROL_TRUNCATE = "b27e3b8"  # titled board -> 'PLACEHOLDER'
CONTROL_CLEAN = "1fd3956"     # an honest append onto a broken board: 0 -> 1


class Finding:
    def __init__(self, severity: str, commit: str, kind: str, detail: str) -> None:
        self.severity = severity
        self.commit = commit
        self.kind = kind
        self.detail = detail


def git(*args: str) -> str:
    """Run git in this file's repository and return stdout ('' on failure)."""
    root = Path(__file__).resolve().parent.parent
    try:
        out = subprocess.run(
            ("git", "-C", str(root)) + args,
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return ""
    return out.stdout if out.returncode == 0 else ""


def git_ok(*args: str) -> bool:
    """Did git succeed? For commands whose answer is the exit status, not text."""
    root = Path(__file__).resolve().parent.parent
    try:
        return subprocess.run(
            ("git", "-C", str(root)) + args,
            capture_output=True, text=True, check=False,
        ).returncode == 0
    except OSError:
        return False


def board_at(ref: str) -> str | None:
    """BOARD.md at `ref`, or None when it is not readable there.

    `git()` returns stdout, and `cat-file -e` prints nothing on success, so it
    cannot be asked whether a blob exists — hence `git_ok`. Worth naming
    because the first draft asked `git()` anyway and got a falsy answer for
    every ref, including the ones that were there.
    """
    if not git_ok("cat-file", "-e", f"{ref}:{BOARD}"):
        return None
    return git("show", f"{ref}:{BOARD}")


def entry_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if LOOKS_LIKE_HEADING.match(line))


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def has_title(text: str) -> bool:
    """Is there a level-1 heading above the first entry?

    ERRATUM, and the reason this is not a string comparison. The first version
    asked whether the board's first line was exactly `# Board`. That is a
    locator fitted to one state of the file, and it broke on the first board
    that was actually in good order: PR #208's restore titles the board
    `# BOARD` and puts an HTML comment above it, so a correct board failed the
    check while nothing about the failure it detects had changed.

    What the 190 placeholder boards actually have in common is not a wrong
    title. It is no title: `PLACEHOLDER`, `WILL_REPLACE`,
    `$(cat /tmp/BOARD_full.md)` and the rest carry no level-1 heading at all
    before the first entry -- all 190 of them. So ask that instead. It catches
    every case the string comparison caught, and it survives the board being
    retitled, which the string comparison did not.
    """
    for line in text.splitlines():
        if LOOKS_LIKE_HEADING.match(line):
            return False          # reached an entry with no title above it
        if LOOKS_LIKE_TITLE.match(line):
            return True
    return False


def subject(ref: str) -> str:
    return git("log", "-1", "--format=%s", ref).strip()


def commits_touching_board(ref: str, limit: int | None) -> list[str]:
    args = ["log", "--format=%h", "--first-parent"]
    if limit:
        args.append(f"-{limit}")
    args += [ref, "--", BOARD]
    return [c for c in git(*args).split() if c]


def classify(parent_text: str, text: str, line: str) -> list[tuple[str, str]]:
    """The whole judgement, on two board texts and a commit subject.

    Pure, so it can be tested without a git history — the same shape as
    `check_board.py`'s `scan_board(text)`. `scan` below supplies the texts and
    the stretch length; everything that decides anything is here.
    """
    out: list[tuple[str, str]] = []
    here, parent = entry_count(text), entry_count(parent_text)

    if not has_title(text) and has_title(parent_text):
        out.append((
            "board truncated to a placeholder",
            f"the level-1 heading is gone; the board now begins "
            f"{first_line(text)[:64]!r}",
        ))
    if here < parent:
        out.append((
            "board shrank",
            f"{parent} entries -> {here} ({here - parent}) — {line!r}",
        ))
    elif CLAIMS_RESTORE.search(line) and here <= parent:
        out.append((
            "restore that did not restore",
            f"subject claims a restore, entries {parent} -> {here} — {line!r}",
        ))
    return out


def scan(ref: str, limit: int | None = None) -> tuple[list[Finding], dict]:
    """Findings, plus the surface-vs-record summary. Newest commit first."""
    commits = commits_touching_board(ref, limit)
    boards = {c: board_at(c) for c in commits}
    counts = {c: entry_count(t) for c, t in boards.items() if t is not None}
    titled = {c: has_title(t) for c, t in boards.items() if t is not None}

    findings: list[Finding] = []
    for i, commit in enumerate(commits):
        text = boards.get(commit)
        parent_text = board_at(f"{commit}^")
        if text is None or parent_text is None:
            continue  # root commit, or the board not yet present
        line = subject(commit)
        for kind, detail in classify(parent_text, text, line):
            if kind == "board truncated to a placeholder":
                # How long did the stretch last? Walk towards `ref` (lower
                # indices) until a board that begins with the title again.
                run = 0
                for j in range(i - 1, -1, -1):
                    if titled.get(commits[j], True):
                        break
                    run += 1
                detail += f"; {run} later commit(s) appended onto it — {line!r}"
            findings.append(Finding(PROBLEM, commit, kind, detail))

    tally: dict[str, int] = {}
    for c in commits:
        if boards.get(c) is not None and not titled.get(c, True):
            key = first_line(boards[c])
            tally[key] = tally.get(key, 0) + 1

    summary = {
        "commits": len(commits),
        "untitled": sum(1 for c in commits if not titled.get(c, True)),
        "first_lines": sorted(tally.items(), key=lambda kv: -kv[1]),
        "here": counts.get(commits[0]) if commits else None,
        "peak": max(counts.items(), key=lambda kv: kv[1]) if counts else None,
    }
    return findings, summary


def report(ref: str, limit: int | None) -> int:
    findings, s = scan(ref, limit)
    problems = [f for f in findings if f.severity == PROBLEM]

    # The surface-vs-record finding first: it is the one with a remedy attached.
    if s["peak"] and s["here"] is not None and s["here"] < s["peak"][1]:
        peak_commit, peak_n = s["peak"]
        problems.insert(0, Finding(
            PROBLEM, ref, "surface holds fewer entries than the record",
            f"{s['here']} entries here, {peak_n} at {peak_commit} "
            f"({s['here'] - peak_n}). Recover with: "
            f"git show {peak_commit}:{BOARD}",
        ))
        findings.insert(0, problems[0])

    notes = [f for f in findings if f.severity == NOTE]
    for f in findings:
        print(f"  {f.commit}: {f.severity}: {f.kind}")
        print(f"      {f.detail}")

    print(f"\n{len(problems)} problem(s), {len(notes)} note(s) "
          f"in {BOARD} history at {ref}.")
    print(f"  {s['commits']} commit(s) touched {BOARD}; {s['untitled']} left a "
          f"file with no level-1 heading, beginning instead:")
    for line, n in s["first_lines"]:
        print(f"      {n:4d}  {line[:68]!r}")
    if not findings:
        print("The board only grew across the commits examined.")
    return 1 if problems else 0


def selftest() -> int:
    """Every control, printed. A check that only ever passes proves nothing."""
    ok = True

    def counts(ref):
        t, p = board_at(ref), board_at(f"{ref}^")
        if t is None or p is None:
            return None, None, "", ""
        return entry_count(t), entry_count(p), first_line(t), first_line(p)

    here, before, _, _ = counts(CONTROL_SHRINK)
    caught = here is not None and here < before
    print(f"  control CAUGHT  {CONTROL_SHRINK} shrink:    {before} -> {here} "
          f"{'OK' if caught else 'FAILED — the wipe is not detected'}")
    ok &= bool(caught)

    t, pt = board_at(CONTROL_TRUNCATE), board_at(f"{CONTROL_TRUNCATE}^")
    trunc = t is not None and pt is not None and has_title(pt) and not has_title(t)
    print(f"  control CAUGHT  {CONTROL_TRUNCATE} truncate:  titled -> "
          f"{first_line(t or '')[:28]!r} "
          f"{'OK' if trunc else 'FAILED — the truncation is not detected'}")
    ok &= bool(trunc)

    # The board this session is proposing on #223 must NOT trip the check. It
    # is the case that found the defect above, so it is a control now.
    u = board_at("origin/claude/board-restore")
    if u is not None:
        good = has_title(u)
        print(f"  control CLEARED #208 restore: {first_line(u)[:28]!r} "
              f"{'OK' if good else 'FAILED — a correct board is flagged'}")
        ok &= bool(good)

    here, before, _, _ = counts(CONTROL_CLEAN)
    clean = here is not None and here >= before
    print(f"  control CLEARED {CONTROL_CLEAN} append:    {before} -> {here} "
          f"{'OK' if clean else 'FAILED — an ordinary append is flagged'}")
    ok &= bool(clean)

    print("\nselftest: " + ("all controls behaved" if ok else "CONTROLS BROKEN"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1])
        del args[i:i + 2]
    ref = args[0] if args else ("origin/main" if git("rev-parse", "--verify",
                                                     "origin/main") else "HEAD")
    return report(ref, limit)


if __name__ == "__main__":
    raise SystemExit(main())
