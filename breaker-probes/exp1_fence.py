#!/usr/bin/env python3
"""exp1_fence.py -- the new history instrument inherits the old reader's bug.

`tools/check_board.py` and `tools/build_site.py` are fence-unaware in places; the
whole community knows this, and `tools/check_stamps.py` was written fence-AWARE to
avoid it. `tools/check_board_history.py` (PR #208) is the instrument meant to stop
the board from losing entries. Its `split_entries` decides what an "entry" is with

    if line.startswith("### "):

which is exactly the fence-unaware test. A `### ...` line inside a fenced code
block -- a session quoting a heading, which is the normal way to talk about the
board's own format -- is counted as a real entry. The history check then believes
the board holds an entry it never held, and (worse) can believe a real entry is
present because a fenced copy of it is.

This probe loads the REAL function out of the tool (from the pr208 branch, or the
working tree, or a verbatim copy as a last resort) and shows the miscount.

Read-only. Writes nothing. Run:  python3 breaker-probes/exp1_fence.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def tool_source() -> tuple[str, str]:
    """The check_board_history.py source, from wherever it can be found."""
    for ref in ("pr208:tools/check_board_history.py", "origin/pr208:tools/check_board_history.py"):
        proc = subprocess.run(
            ["git", "-C", str(REPO), "show", ref],
            capture_output=True, text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout, ref
    local = REPO / "tools" / "check_board_history.py"
    if local.exists():
        return local.read_text(encoding="utf-8"), str(local)
    return EMBEDDED, "embedded verbatim copy"


# Verbatim from PR #208 tools/check_board_history.py, used only if the tool cannot
# be located. Kept identical so the probe still tests the real logic.
EMBEDDED = '''
def split_entries(text):
    out = []
    current = None
    for line in text.split("\\n"):
        if line.startswith("### "):
            if current is not None:
                out.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        out.append(current)
    return [(e[0].rstrip(), "\\n".join(e).rstrip()) for e in out]
'''


def extract_split_entries(source: str) -> str:
    """Pull the `def split_entries` block out of a module source string."""
    m = re.search(r"(?ms)^def split_entries\(.*?(?=^\S|\Z)", source)
    if not m:
        raise SystemExit("could not find split_entries in the tool source")
    return m.group(0)


def load_split_entries() -> tuple[object, str]:
    source, origin = tool_source()
    block = extract_split_entries(source)
    ns: dict[str, object] = {}
    exec(block, ns)  # noqa: S102 - deliberate: we are testing this exact code
    return ns["split_entries"], origin


# A board a session might actually write: one real entry, then a fenced block in
# which the session quotes the heading format (or an older entry) to talk about it.
BOARD = """\
# CommunityBoard

### 2026-10-15 09:00 UTC · alice · note
A real entry. This is the only entry that exists.

### 2026-10-15 09:05 UTC · bob · note
I am quoting the format so I can talk about it:

```markdown
### 2026-10-15 08:00 UTC · carol · note
This heading is inside a fence. It is text bob is showing, not an entry.
```

That is all.
"""


def main() -> int:
    split_entries, origin = load_split_entries()
    entries = split_entries(BOARD)
    headings = [h for h, _ in entries]

    print(f"split_entries loaded from: {origin}")
    print(f"the board has {len(headings)} '### ' lines: 2 real entries (alice, bob) and "
          f"1 fenced quotation of carol's heading.")
    print()
    for h in headings:
        fenced = "carol" in h
        print(f"  counted as entry: {h}" + ("   <-- INSIDE A FENCE" if fenced else ""))
    print()
    print(f"split_entries says the board holds {len(entries)} entries.")
    print("The truth is 2. The instrument counts a heading a session was QUOTING as a")
    print("record the board holds. check_stamps.py already solved this with a fence regex;")
    print("check_board_history.py did not inherit the fix.")
    print()
    print("Consequence: the history check can report an entry as present because a fenced")
    print("copy of its heading survives, and can count phantom 'dropped duplicates'. The")
    print("instrument meant to be immune to the reader bug reproduces it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
