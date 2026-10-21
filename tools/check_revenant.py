#!/usr/bin/env python3
"""check_revenant.py: find commits that return a file to a state it had already left.

A *revenant* is a commit whose new content for a path is byte-identical to content that path
held at some earlier ancestor, but not at the commit's own parent. Git cannot tell a revenant
from an edit. A session that writes a whole file from a stale copy in its context produces a
commit whose diff reads "undo everything since my copy", and a three-way merge honours that
diff, because the other side did not touch those lines.

That is how `made/README.md` lost its #204 repair. The repair merged at `cb501d8` on
2026-10-14 21:09 UTC. Three hours later `8005afc` (the quoin) wrote the file from a copy taken
before the repair; its blob is byte-for-byte the pre-repair blob. The merge `f040c91` saw one
side remove `# made/` and the other side not touch it, and removed it. Nothing was red.
`check_made.py` passed, correctly: the index was intact, and nobody had asked the other
question. The same shape, on `BOARD.md`, is #209's ten emptyings.

Two kinds are reported. A commit whose blob equals an ancestor's but not its parent's (the
quoin commit itself). And a merge whose three-way result equals neither parent yet matches an
older state (`f040c91`: one side had dropped `# made/`, the other lacked a blank line, and the
merged bytes were exactly the file of 2026-10-11). A merge that simply adopts its branch's
version is not reported; the branch had it, nothing returned.

Returning to a prior state is sometimes right. A revert is one, on purpose, and says so in
its subject. So this check names revenants; it does not decide.

    python3 tools/check_revenant.py                   # every path reachable from HEAD
    python3 tools/check_revenant.py made/README.md    # one path
    python3 tools/check_revenant.py --since 2026-10-14
    python3 tools/check_revenant.py --ref origin/main

Exit 1 if any revenant is found, 0 otherwise. Standard library only; reads, writes nothing.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from functools import lru_cache


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


@lru_cache(maxsize=None)
def blob_at(commit: str, path: str) -> str | None:
    """The blob id of path at commit, or None if absent."""
    r = subprocess.run(["git", "rev-parse", "--verify", "-q", f"{commit}:{path}"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


@lru_cache(maxsize=None)
def is_ancestor(a: str, b: str) -> bool:
    """True if commit a is an ancestor of commit b (or equal)."""
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                          capture_output=True).returncode == 0


def touches(ref: str, path: str | None, since: str | None):
    """Yield (commit, parents, date, subject, {path: (old_blob, new_blob, status)}), oldest first.

    Walks every parent, not just the first, so a stale write on a side branch is seen where it
    happened and not only where a merge carried it to main.
    """
    # For a merge, diff against its first parent only; the second-parent side is reached when
    # the walk visits that branch's own commits.
    cmd = ["log", ref, "--format=%x00%H%x01%P%x01%cd%x01%s", "--date=iso-strict-local",
           "--raw", "--abbrev=40", "--no-renames", "--reverse", "--diff-merges=first-parent"]
    if since:
        cmd.append(f"--since={since}")
    cmd.append("--")
    if path:
        cmd.append(path)
    out = git(*cmd)
    commit = None
    # Yield each commit only after its --raw lines have been read. An earlier draft yielded
    # the tuple on the header line, before the dict was filled, and saw an empty dict every
    # time: zero revenants in a history with a known one. Same shape as the thing being
    # checked, a reader acting on a state its writer had not finished.
    for line in out.split("\n"):
        if line.startswith("\x00"):
            if commit is not None:
                yield commit
            h, parents, d, s = line[1:].split("\x01", 3)
            commit = (h, parents.split(), d[:16].replace("T", " "), s, {})
        elif line.startswith(":") and commit is not None:
            meta, _, p = line.partition("\t")
            parts = meta.split()
            commit[4][p] = (parts[2], parts[3], parts[4][0])
    if commit is not None:
        yield commit


def find_revenants(ref: str, path: str | None, since: str | None):
    """Return {path: [(commit, date, subject, earlier_commit, earlier_date, earlier_subject)]}."""
    # path -> blob -> [(commit, date, subject)] for every commit that produced that blob
    producers: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    found: dict[str, list] = defaultdict(list)
    for h, parents, d, s, changes in touches(ref, path, since):
        for p, (old, new, status) in changes.items():
            if status == "D":
                new = "<deleted>"
            if new != "<deleted>" and new != old and producers[p].get(new):
                # An earlier commit produced this exact blob. It is a revenant if (a) that
                # commit is in our past, not a sibling that converged on the same bytes, and
                # (b) no parent of this commit holds the blob: a merge that adopts its
                # branch's version is not a return, the branch simply had it.
                if any(blob_at(par, p) == new for par in parents):
                    pass
                else:
                    for (eh, ed, es) in producers[p][new]:
                        if eh != h and is_ancestor(eh, h):
                            found[p].append((h, d, s, eh, ed, es))
                            break
            producers[p][new].append((h, d, s))
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", nargs="?", help="one path; default is every path")
    ap.add_argument("--ref", default="HEAD", help="walk history reachable from this ref")
    ap.add_argument("--since", help="only commits after this date, e.g. 2026-10-14")
    ap.add_argument("--quiet", action="store_true", help="summary line only")
    a = ap.parse_args(argv)

    found = find_revenants(a.ref, a.path, a.since)
    total = sum(len(v) for v in found.values())
    if not a.quiet:
        for p in sorted(found):
            print(p)
            for h, d, s, eh, ed, es in found[p]:
                print(f"  {h[:7]} {d}  {s[:72]}")
                print(f"     returned the file to its state at {eh[:7]} {ed}  {es[:50]}")
        if found:
            print()
    scope = a.path or "all paths"
    print(f"{total} revenant(s) in {len(found)} path(s); {scope} from {a.ref}"
          + (f", since {a.since}" if a.since else "") + ".")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
