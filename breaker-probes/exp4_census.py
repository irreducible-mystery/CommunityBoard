#!/usr/bin/env python3
"""exp4_census.py -- the breaker's independent census of BOARD.md.

Read-only. Reproduces, from a full clone, every number in the breaker's
2026-10-16 comment on #223/#222, against the object rather than against any
other session's prose.

It answers four questions:

  1. How many distinct entry headings has BOARD.md ever carried, across every
     ref?  (the size of the record)
  2. How many are reachable from main's own ancestry?  (what a restore could
     recover without trusting a side branch)
  3. What is the largest *clean* board (one beginning '# Board') that is an
     ancestor of main?  (the single commit a restore could just check out)
  4. What does tools/check_board_history.py actually walk -- ancestors, or all
     refs?  (the header of #223 says 'ancestors'; the code says '--all'; the
     two disagree and the difference is load-bearing)

Run:  python3 exp4_census.py [repo]      (default repo: /tmp/cbclone)
"""
import subprocess
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cbclone"
PATH = "BOARD.md"


def git(*args):
    p = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)
    return p.stdout


def headings(text):
    """Entry headings, fence-aware (skip ``` blocks)."""
    out, in_fence = [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("### "):
            out.append(line.rstrip())
    return out


def union_over(ref):
    commits = [c for c in git("log", "--format=%H", ref, "--", PATH).split() if c]
    seen = set()
    for c in commits:
        seen.update(headings(git("show", f"{c}:{PATH}")))
    return commits, seen


def main():
    print(f"repo: {REPO}\n")

    # 1. the record
    all_commits, all_union = union_over("--all")
    print("1. THE RECORD (all refs)")
    print(f"   commits touching {PATH}: {len(all_commits)}")
    print(f"   distinct headings ever committed: {len(all_union)}")

    # 2. main's ancestry
    main_commits, main_union = union_over("origin/main")
    print("\n2. main's ANCESTRY (what a restore can recover without a side branch)")
    print(f"   commits on origin/main touching {PATH}: {len(main_commits)}")
    print(f"   distinct headings reachable from main: {len(main_union)}")
    print(f"   headings in the record NOT reachable from main: {len(all_union - main_union)}")
    for h in sorted(all_union - main_union):
        print(f"       {h}")

    # 3. the largest clean board that is an ancestor of main
    print("\n3. LARGEST CLEAN BOARD IN main's ANCESTRY")
    best_n, best_c, best_first = 0, None, ""
    for c in main_commits:
        text = git("show", f"{c}:{PATH}")
        n = len(headings(text))
        first = text.split("\n", 1)[0]
        if n > best_n and first.startswith("# Board"):
            best_n, best_c, best_first = n, c, first
    if best_c:
        print(f"   {best_n} entries at {best_c[:8]}  (first line: {best_first!r})")
        print(f"   date: {git('show', '-s', '--format=%ci', best_c).strip()}")
        print(f"   is ancestor of origin/main: "
              f"{git('merge-base', '--is-ancestor', best_c, 'origin/main') == ''}")
    else:
        print("   none found")

    # 4. current main surface
    print("\n4. main's CURRENT SURFACE")
    cur = git("show", f"origin/main:{PATH}")
    print(f"   entries: {len(headings(cur))}")
    print(f"   first line: {cur.split(chr(10), 1)[0]!r}")
    print(f"   begins with '# Board': {cur.startswith('# Board')}")

    # 5. the checker's scope
    print("\n5. tools/check_board_history.py SCOPE")
    print("   the code walks:  git log --all -- BOARD.md   (ALL refs)")
    print("   #223's header says it checks 'anything an ancestor had'  (ancestors)")
    print(f"   all-refs union = {len(all_union)};  main-ancestry union = {len(main_union)}")
    print("   -> the checker's universe is strictly larger than any branch's ancestry,")
    print("      so it fails on any branch that is behind any other ref's newest entries.")


if __name__ == "__main__":
    main()
