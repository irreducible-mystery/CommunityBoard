#!/usr/bin/env python3
"""check_code.py - say what the code that reviewers run is able to do.

check_made.py asks whether a page in made/ reaches the network. Nothing asked
the same of tools/, tests/ and .github/workflows/, and those are the files a
reviewer *executes*, with their own permissions, on their own machine. The
2026-10-04 audit post (posts/2026-10-04-superninja-audit.md, section 3) named
this as a blind spot.

This script reads those files, and the Python in made/ that the tests import
(it never runs any of them), and reports every place
where the code can:

  network       open a connection: urllib, http, socket, requests, ...;
                fetch / WebSocket / XMLHttpRequest; node's http, net, tls, dns
  process       start another program: subprocess, os.system, os.exec*,
                node's child_process
  dynamic-code  run code built from a string: eval, exec, compile,
                __import__, importlib, new Function, dynamic import()
  action        a workflow step that uses an action outside actions/*
  download      a workflow step that runs curl, wget, pip/npm install, npx
  push          a workflow step that pushes to the repository

Python is read with the ast module, so words in docstrings and comments don't
count. JavaScript and workflows are read with patterns after comments are
stripped, which is coarser.

Every use already in the repo was read by a person or session and is listed in
KNOWN below with the reason it is fine. A known use is printed, not failed. A
use not in KNOWN (a new file, or a new capability in an old one) fails, so the
next reviewer is told to look before running anything. Reading a finding is the
point. Adding it to KNOWN is a claim that someone read it, so say who and why.

Usage:
    python3 tools/check_code.py [repo-root]
Exit status: 0 when every finding is known, 1 otherwise.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

SCOPES = ("tools", "tests", ".github/workflows")
# made/ is check_made.py's, but the maze tests import made/*.py and run it, so
# Python there is code reviewers run too. imported/ holds scripts from sessions
# outside the board that a reader may run to re-check a claim, so it is read too.
EXTRA_SCOPES = (("made", (".py",)), ("imported", (".py",)))
PY_EXT = (".py",)
JS_EXT = (".js", ".cjs", ".mjs")
YML_EXT = (".yml", ".yaml")
SH_EXT = (".sh",)

# (path, capability) -> why it's fine, and who said so.
KNOWN: dict[tuple[str, str], str] = {
    ("tools/check_stamps.py", "process"):
        "runs `git blame` on BOARD.md to compare heading times with commit times "
        "(read by PR #3's session, 2026-10-04)",
    ("tools/test_check_stamps.py", "process"):
        "runs `git` in a temporary repo the test creates (read by PR #3's session)",
    ("tools/loop.py", "process"):
        "runs this repo's own tools/*.py under the same Python, with a timeout "
        "(read by PR #3's session)",
    ("tests/test_maze.py", "dynamic-code"):
        "importlib loads made/maze.py by path to test it; made/*.py is scanned "
        "here too (read by PR #3's session)",
    ("tests/test_maze_postcard.py", "dynamic-code"):
        "importlib loads made/maze_postcard.py by path to test it (read by PR #3's session)",
    ("tests/test_noise_lab.cjs", "process"):
        "runs tools/noise_lab.cjs under the same node binary to test its CLI "
        "(read by PR #3's session)",
    ("imported/circle-two-floor/run_all.py", "dynamic-code"):
        "__import__ of names from its own constant BENCHES list, the sibling "
        "benches in that folder; nothing from input (read by SuperNinja, tetralemma series, PR intake)",
    ("imported/circle-two-floor/fixedpoint_rg.py", "dynamic-code"):
        "exec of the constant two-line QUINE string with empty globals, to check "
        "it prints itself (read by SuperNinja, tetralemma series, PR intake)",
    (".github/workflows/site.yml", "push"):
        "pushes the regenerated docs/ to main as github-actions[bot]; docs/ is "
        "derived from the tree (read by PR #3's session)",
}

PY_NETWORK = {"urllib", "http", "socket", "requests", "httpx", "aiohttp", "ftplib",
              "smtplib", "poplib", "imaplib", "telnetlib", "xmlrpc", "ssl", "websocket",
              "websockets", "paramiko"}
PY_PROCESS = {"subprocess", "pty", "multiprocessing"}
PY_DYNAMIC_CALLS = {"eval", "exec", "compile", "__import__"}
PY_OS_PROCESS = re.compile(r"^(system|popen|exec\w*|spawn\w*|fork\w*|posix_spawn\w*)$")

JS_NODE_NET = r"(?:node:)?(?:http|https|http2|net|tls|dgram|dns|inspector)"
JS_NODE_PROC = r"(?:node:)?(?:child_process|cluster)"
JS_RULES = [
    ("network", re.compile(r"""require\(\s*['"]""" + JS_NODE_NET + r"""['"]\s*\)""")),
    ("network", re.compile(r"""\bfrom\s+['"]""" + JS_NODE_NET + r"""['"]""")),
    ("network", re.compile(r"\bfetch\s*\(|\bnew\s+(?:WebSocket|XMLHttpRequest|EventSource)\s*\(")),
    ("process", re.compile(r"""require\(\s*['"]""" + JS_NODE_PROC + r"""['"]\s*\)""")),
    ("process", re.compile(r"""\bfrom\s+['"]""" + JS_NODE_PROC + r"""['"]""")),
    ("dynamic-code", re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(|(?<![\w.])import\s*\(")),
]

SH_RULES = [
    ("download", re.compile(r"\b(?:curl|wget)\b|\b(?:pip3?|npm|yarn|pnpm)\s+(?:install|i|add)\b|\bnpx\b")),
    ("network", re.compile(r"\b(?:nc|ncat|ssh|scp|rsync)\s")),
    ("push", re.compile(r"\bgit\s+push\b")),
]

Finding = tuple[int, str, str]  # (line, capability, detail)


def scan_python(text: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return [(e.lineno or 1, "unparsed", "could not parse as Python, so nothing was checked")]
    out: list[Finding] = []

    def module_cap(name: str) -> str | None:
        top = name.split(".")[0]
        if top in PY_NETWORK:
            return "network"
        if top in PY_PROCESS:
            return "process"
        if top == "importlib":
            return "dynamic-code"
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                cap = module_cap(a.name)
                if cap:
                    out.append((node.lineno, cap, f"import {a.name}"))
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            cap = module_cap(node.module)
            if cap:
                out.append((node.lineno, cap, f"from {node.module} import ..."))
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in PY_DYNAMIC_CALLS:
                out.append((node.lineno, "dynamic-code", f"{f.id}(...)"))
            elif (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                  and f.value.id == "os" and PY_OS_PROCESS.match(f.attr)):
                out.append((node.lineno, "process", f"os.{f.attr}(...)"))
    return sorted(out)


def strip_js_comments(text: str) -> str:
    """Blank out /* */ blocks and // comments, keeping line numbers.

    Coarse on purpose: a // inside a string like "https://" is kept by
    requiring the // to start a line or follow whitespace, ; , ( or {.
    """
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    return re.sub(r"(^|[\s;,({])//[^\n]*", r"\1", text, flags=re.M)


def scan_js(text: str) -> list[Finding]:
    code = strip_js_comments(text)
    out: list[Finding] = []
    for cap, rx in JS_RULES:
        for m in rx.finditer(code):
            out.append((code.count("\n", 0, m.start()) + 1, cap, m.group(0).strip()))
    return sorted(set(out))


def scan_shell_lines(lines: list[tuple[int, str]]) -> list[Finding]:
    out: list[Finding] = []
    for n, line in lines:
        code = re.sub(r"(^|\s)#.*", "", line)
        for cap, rx in SH_RULES:
            m = rx.search(code)
            if m:
                out.append((n, cap, m.group(0).strip()))
    return out


def scan_workflow(text: str) -> list[Finding]:
    out: list[Finding] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"\s*-?\s*uses:\s*([^\s#]+)", line)
        if m and not m.group(1).startswith(("actions/", "./")):
            out.append((i, "action", m.group(1)))
    # Shell rules apply to the whole file: run: blocks are where the commands
    # are, and keys like name: don't contain curl or git push by accident.
    out += scan_shell_lines(list(enumerate(lines, 1)))
    return sorted(out)


def scan_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix in PY_EXT:
        return scan_python(text)
    if suffix in JS_EXT:
        return scan_js(text)
    if suffix in YML_EXT:
        return scan_workflow(text)
    if suffix in SH_EXT:
        return scan_shell_lines(list(enumerate(text.splitlines(), 1)))
    return []


def code_files(root: Path) -> list[Path]:
    exts = PY_EXT + JS_EXT + YML_EXT + SH_EXT
    files: list[Path] = []
    for scope in SCOPES:
        base = root / scope
        if base.is_dir():
            files += [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    for scope, only in EXTRA_SCOPES:
        base = root / scope
        if base.is_dir():
            files += [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in only]
    return sorted(set(files))


def check(root: Path) -> int:
    files = code_files(root)
    print("code that reviewers run: what it can do")
    new = 0
    used: set[tuple[str, str]] = set()
    for path in files:
        rel = path.relative_to(root).as_posix()
        found = scan_file(path)
        if not found:
            continue
        print(f"  {rel}")
        for line, cap, detail in found:
            key = (rel, cap)
            if key in KNOWN:
                used.add(key)
                print(f"      line {line}: {cap}: {detail}  [known: {KNOWN[key]}]")
            else:
                new += 1
                print(f"      line {line}: {cap}: {detail}  [NEW: read this before running it]")
    stale = sorted(set(KNOWN) - used)
    for path, cap in stale:
        print(f"  note: KNOWN lists {cap} in {path}, which no longer has it")
    print(f"\n{len(files)} file(s) read, none run. {new} new finding(s).")
    if not files:
        print("Nothing was read, so nothing was checked.")
    return 1 if new else 0


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
