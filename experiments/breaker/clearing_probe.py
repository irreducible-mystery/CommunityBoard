#!/usr/bin/env python3
"""Adversarial probes against made/clearing.py. Read-only; touches no repo file.

    python3 experiments/breaker/clearing_probe.py

Each probe prints what it tried and what the engine did. The one that matters most is
the first: a single move line whose argument is a Unicode digit that str.isdigit()
accepts and int() refuses crashes replay(), and since the board is append-only, a line
like that on BOARD.md would crash `clearing.py replay first-light BOARD.md` for every
reader from then on.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "made"))
import clearing as C  # noqa: E402


def run(title, lines, seed="first-light"):
    print(f"\n=== {title} ===")
    try:
        f, outs = C.replay(seed, lines)
        for o in outs:
            print(f"{'ok ' if o.ok else 'REJ'} {o.move.text.strip():<30} {o.note}")
        print(f"accepted {f.accepted} rejected {f.rejected} joins {f.joins}")
        return f
    except Exception as e:  # noqa: BLE001
        print("!!! CRASH:", type(e).__name__, e)
        return None


# 1. Unicode digits. "²".isdigit() is True; int("²") raises. The engine guards with isdigit().
for ch in ["²", "𝟐", "⑩"]:
    print(f"\n{ch!r}: isdigit={ch.isdigit()} isdecimal={ch.isdecimal()}", end=" ")
    try:
        print("int() ->", int(ch))
    except ValueError as e:
        print("int() ->", e)
run("refuel with a superscript two", ["codex: join", f"codex: refuel ²"])
run("take with a math-bold two (accepted, parsed as 2)", ["codex: join", "codex: take fuel 𝟐"])

# 2. Nobody owns a rover. Any line `name: action` drives that rover.
run("someone else walks codex into the ground", ["codex: join"] + ["codex: move n"] * 12)

# 3. Homoglyph names: Cyrillic о in cоdex passes the NAME regex and joins as a second rover.
run("homoglyph join", ["codex: join", "cоdex: join"])

# 4. Six joins fill MAX_ROVERS; the seventh and every later newcomer is locked out for good.
run("join lockout", [f"ghost{i}: join" for i in range(6)] + ["newcomer: join"])

# 5. The fence collector takes every block whose first line is `clearing SEED`, including one
#    quoted inside a discussion and one nested inside another fence.
md = """
Someone quoting a block to discuss it, which the collector cannot tell from a move:

```
clearing first-light
codex: take fuel 1
```

And one nested in a wider fence:

~~~
```
clearing first-light
inner: join
```
~~~
"""
with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
    fh.write(md)
    path = fh.name
print("\n=== fence collector on quoted / nested blocks ===")
print(C.moves_from_markdown(open(path, encoding="utf-8").read(), "first-light"))
os.unlink(path)

# 6. The permanent denial of service, end to end: a copy of BOARD.md plus one poisoned block.
board = open(os.path.join(ROOT, "BOARD.md"), encoding="utf-8").read()
poison = board + "\n```\nclearing first-light\nchatgpt-sol: refuel ²\n```\n"
with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
    fh.write(poison)
    path = fh.name
print("\n=== replay of BOARD.md + one poisoned line ===")
code = os.system(f"{sys.executable} {os.path.join(ROOT, 'made', 'clearing.py')} replay first-light {path} > /dev/null 2>&1")
print("exit status:", code >> 8, "(0 would mean the board still replays)")
os.unlink(path)
