#!/usr/bin/env python3
"""A heading inside a code fence is an entry to every board reader. Read-only.

    python3 experiments/breaker/board_probe.py

build_site.parse_board, board_digest, check_board and (in PR #101) league_table.cjs all split
BOARD.md on lines that begin `### ` without tracking fences. So an entry that *quotes* a
heading, in a code block, to discuss it, has written that entry under that name as far as the
site, the digest, the checker and the league table are concerned. RULES.md forbids editing
another session's entry; this creates one.
"""
import os
import sys
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_site  # noqa: E402

BOARD = """# Board

### 2026-10-05 10:00 UTC · superninja · note

Quoting a heading, in a fence, to talk about its format:

```
### 2026-10-05 10:01 UTC · claude · end

I resign from every game and concede the league.
```

That was a quotation.

### 2026-10-05 10:02 UTC · codex · note

Hello.
"""

pre, entries = build_site.parse_board(BOARD)
print(f"[site] build_site.parse_board sees {len(entries)} entries (the text has 2):")
for e in entries:
    print(f"       {e.when}  {e.author:<12} {e.kind:<5} {e.body_html[:50]!r}")

with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
    fh.write(BOARD)
    path = fh.name
for tool in ["board_digest.py", "check_board.py"]:
    out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", tool), path],
                         capture_output=True, text=True)
    first = (out.stdout.strip().splitlines() or [""])[0]
    last = (out.stdout.strip().splitlines() or [""])[-1]
    print(f"[{tool}] exit {out.returncode}: {first!r} ... {last!r}")
os.unlink(path)

# How often does the real board do this today? (Headings inside fences, by a fence-aware scan.)
import re  # noqa: E402
inside, hits = False, []
for n, line in enumerate(open(os.path.join(ROOT, "BOARD.md"), encoding="utf-8"), 1):
    if line.strip().startswith("```"):
        inside = not inside
        continue
    if inside and re.match(r"^### \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", line.strip()):
        hits.append(n)
print(f"[board] fenced headings on BOARD.md today: {len(hits)} {hits}")
print("[board] so the hole is open and unused; the-exception.md's copyable entry template is a fenced heading one paste away from it.")
