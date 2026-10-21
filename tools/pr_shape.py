#!/usr/bin/env python3
"""pr_shape.py: say what merging each open pull request would actually do to main.

Usage:  git fetch origin main '+refs/pull/*/head:refs/remotes/pr/*'
        python3 tools/pr_shape.py [--base origin/main] [REF ...]

With no REF it reads every `refs/remotes/pr/*`. For each it prints, against the base:

- **merge**: `clean` if `git merge-tree` finds no conflict, `conflict` (with the paths)
  if it does, `in-base` if every commit is already in the base (a merged or emptied PR;
  `refs/pull/*` includes closed ones), and `no-base` if the two share no commit in this
  clone.
- **behind / ahead**: commits on the base since the fork point, and on the PR.
- **shape**: how many files it adds, modifies and deletes. A PR that only adds is the
  easy case; one that deletes on a stale branch is the one to read first.
- **touches**: whether it changes the board (`BOARD.md`, `board/`), the rules
  (`RULES.md`, `CLAUDE.md`, `AGENTS.md`), or CI (`.github/`). Those go to the steward.

Why `no-base` is its own answer: this repository is often cloned shallow. In a shallow
clone an old PR shares no commit with `main`, `git merge-tree` fails, and a script that
reads any failure as a conflict reports twenty-two mergeable pull requests as conflicted.
The first draft of the triage this tool came from did exactly that. Run
`git fetch --unshallow origin` and the `no-base` rows resolve into real answers.

It does not read CI, reviews, or comments: whether a PR is *ready* is a judgement about
those, and this only answers what the merge would do. Read-only; it writes no refs and
no files. Exits 0. Standard library and git (2.38 or later, for `merge-tree --write-tree`).
"""
import argparse
import subprocess
import sys

RULES = ("RULES.md", "CLAUDE.md", "AGENTS.md")
CI = (".github/",)


def git(*args, check=True):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def pr_refs():
    out = git("for-each-ref", "--format=%(refname)", "refs/remotes/pr/").stdout.split()
    tail = lambda r: r.rsplit("/", 1)[-1]
    # Newest PR first; names that are not numbers go last.
    return sorted(out, key=lambda r: -int(tail(r)) if tail(r).isdigit() else 1)


def classify(status_lines):
    """Count A/M/D (renames and copies count as modified) and flag sensitive paths."""
    added = modified = deleted = 0
    paths = []
    for line in status_lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        code, path = parts[0][:1], parts[-1]
        paths.append(path)
        if code == "A":
            added += 1
        elif code == "D":
            deleted += 1
        else:
            modified += 1
    touches = []
    if any(p == "BOARD.md" or p.startswith("board/") for p in paths):
        touches.append("board")
    if any(p in RULES for p in paths):
        touches.append("rules")
    if any(p.startswith(CI) for p in paths):
        touches.append("ci")
    return added, modified, deleted, touches


def conflicted_paths(merge_tree_stdout):
    """Paths named in the conflicted-file section of `merge-tree --write-tree` output."""
    paths = []
    lines = merge_tree_stdout.splitlines()[1:]
    for line in lines:
        if not line.strip():
            break
        # "<mode> <object> <stage>\t<path>"
        if "\t" in line:
            path = line.split("\t", 1)[1]
            if path not in paths:
                paths.append(path)
    return paths


def shape(base, ref):
    mb = git("merge-base", base, ref, check=False)
    if mb.returncode != 0:
        return {"ref": ref, "merge": "no-base", "behind": "?", "ahead": "?",
                "added": "?", "modified": "?", "deleted": "?", "touches": [], "conflicts": []}
    fork = mb.stdout.strip()
    behind = git("rev-list", "--count", f"{fork}..{base}").stdout.strip()
    ahead = git("rev-list", "--count", f"{fork}..{ref}").stdout.strip()
    added, modified, deleted, touches = classify(
        git("diff", "--name-status", "-M", f"{base}...{ref}").stdout.splitlines())
    mt = git("merge-tree", "--write-tree", base, ref, check=False)
    conflicts = [] if mt.returncode == 0 else conflicted_paths(mt.stdout)
    merge = "in-base" if ahead == "0" else "clean" if mt.returncode == 0 else "conflict"
    return {"ref": ref, "merge": merge,
            "behind": behind, "ahead": ahead, "added": added, "modified": modified,
            "deleted": deleted, "touches": touches, "conflicts": conflicts}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("refs", nargs="*")
    args = ap.parse_args(argv)
    refs = args.refs or pr_refs()
    if not refs:
        print("no refs given and none under refs/remotes/pr/ — fetch them first:")
        print("  git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'")
        return 0
    if git("rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        print("note: this clone is shallow; old PRs will read no-base until "
              "`git fetch --unshallow origin`\n")
    rows = [shape(args.base, r) for r in refs]
    print(f"{'ref':<22} {'merge':<9} {'behind':>6} {'ahead':>6}  {'+add':>4} {'~mod':>4} {'-del':>4}  touches")
    for r in rows:
        name = r["ref"].removeprefix("refs/remotes/")
        print(f"{name:<22} {r['merge']:<9} {r['behind']:>6} {r['ahead']:>6}  "
              f"{r['added']:>4} {r['modified']:>4} {r['deleted']:>4}  {','.join(r['touches']) or '-'}")
        if r["conflicts"]:
            print(f"{'':<22} conflicts: {', '.join(r['conflicts'])}")
    kinds = ("clean", "conflict", "in-base", "no-base")
    counts = {k: sum(1 for r in rows if r["merge"] == k) for k in kinds}
    print(f"\n{len(rows)} ref(s): " + ", ".join(f"{counts[k]} {k}" for k in kinds) + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
