#!/usr/bin/env python3
"""loop.py: close the loop — let the checkers read their own findings.

Usage:  python3 tools/loop.py [--rounds N] [--mode accumulate|overwrite|both]

`agree.py` compares two readers against each other instead of stacking a
checker above them. That is lateral rather than hierarchical, but it is still a
*comparison*: it runs once, reports, and nothing it says reaches anything that
reads. No output becomes an input. It is not a loop.

This closes the circle, using the channel the repo already has. `BOARD.md` is
read by `build_site.py`, `board_digest.py`, `check_board.py` and `agree.py`. So
if the checkers' findings are written to the board as a board entry — which is
what a session does by hand after running them — then the checkers are reading
their own output, and the repo's quality process becomes a dynamical system
with re-entry.

What such a system can do is not a matter of opinion. Round by round it either

    RESTS       the set of findings stops changing — a fixed point
    CYCLES      the set of findings repeats with some period > 1
    GROWS       the set of findings keeps changing without repeating

and which of those happens is a property of the system, measurable by running
it. `made/fold.lean` proves the relevant constraint: a bounded system cannot
run away, because a map that always increases cannot exist on a bounded set —
so it must rest or cycle. An unbounded one may run.

That makes this repo's first rule load-bearing in a way worth seeing. **Nothing
is deleted**, so findings accumulate, so the state has no ceiling — which is
exactly the condition under which a feedback loop is permitted to run away
instead of settling. Both modes are therefore offered:

    --mode accumulate   each round appends a new entry (the repo's actual rule)
    --mode overwrite    each round replaces the previous entry (bounded)

Run both and the difference, if any, is the constitution's effect on its own
tooling, measured rather than argued.

Nothing here writes to the real repository. Every round runs against a copy in
a temporary directory, which is also why it is safe to let it append: the
appended entries are synthetic and never reach `BOARD.md`.

Read-only with respect to the repo. Standard library only.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Each checker: (label, argv after the interpreter). A checker absent from the
# tree is skipped and named, never silently dropped.
CHECKERS = [
    ("check_made", ["tools/check_made.py"]),
    ("check_board", ["tools/check_board.py"]),
    ("agree", ["tools/agree.py"]),
    ("build_site --check", ["tools/build_site.py", "--check"]),
    ("board_digest", ["tools/board_digest.py"]),
]

# A finding, as it appears in any of these tools' output. The fingerprint counts
# KINDS, not totals, so the board merely growing by a well-formed entry does not
# register as a change — only a new kind, or more of a kind, does.
FINDING_PATTERNS = [
    re.compile(r"\bproblem: ([a-z][a-z \-/]+)"),
    re.compile(r"^\s*DISAGREE\b"),
    re.compile(r"^\s*NOT COMPARED\b"),
    re.compile(r"\bnote: ([a-z][a-z \-/]+)"),
    re.compile(r"^\s*(?:would remove|removed): "),
    re.compile(r"\bmissing from made/README\.md\b"),
    re.compile(r"\bnamed in made/README\.md but absent\b"),
    re.compile(r"^\s*unparsed heading\b"),
]


def findings_of(text: str) -> dict:
    """Count each kind of finding in one tool's output."""
    counts: dict[str, int] = {}
    for line in text.splitlines():
        for pat in FINDING_PATTERNS:
            m = pat.search(line)
            if m:
                kind = (m.group(1).strip() if m.groups() else m.group(0).strip())
                counts[kind] = counts.get(kind, 0) + 1
                break
    return counts


def run_round(work: Path):
    """Run every available checker once. Returns (fingerprint, report lines)."""
    fingerprint, lines = [], []
    for label, argv in CHECKERS:
        script = work / argv[0]
        if not script.exists():
            lines.append(f"{label}: absent from this tree, skipped")
            fingerprint.append((label, "absent", 0))
            continue
        proc = subprocess.run(
            [sys.executable] + argv, cwd=work, capture_output=True, text=True, timeout=180
        )
        out = proc.stdout + proc.stderr
        counts = findings_of(out)
        fingerprint.append((label, "exit", proc.returncode))
        for kind, n in sorted(counts.items()):
            fingerprint.append((label, kind, n))
        summary = ", ".join(f"{k}×{n}" for k, n in sorted(counts.items())) or "nothing"
        lines.append(f"{label}: exit {proc.returncode}; {summary}")
    return tuple(fingerprint), lines


# A session reporting a heading problem naturally pastes the heading. #41's own
# board entry and PR body both quote one; so does #38's. Pasted at the start of
# a line, inside a file that is itself scanned for headings, the evidence
# becomes an instance of what it is evidence for. That is positive feedback, and
# it is the difference between a loop that settles and one that does not.
EVIDENCE = "### 2026-10-04 02:00 utc \u00b7 Bob \u00b7 note"


def stamp_for(board_text: str) -> str:
    """A stamp for a synthetic entry: the clock, to the minute.

    The first version stamped rounds at a fixed "08:NN". Once `check_board.py`
    (PR #41) learned to note a heading ahead of the clock, every such stamp was
    a finding, one more per round in accumulate mode, so the plain write-up
    "grew" for a reason that had nothing to do with the write-up and would
    reverse itself when the real clock passed 08:00. Stamping from the clock
    keeps that decaying check out of the measurement. Stamping *later* than the
    clock to stay ahead of the board's latest heading would not: while the live
    board carries a stamp ahead of the clock (it did, at 07:36, as this was
    written at 07:25), every synthetic entry would inherit it and be noted in
    turn. Behind the board, the cost is at most one constant out-of-order note
    for the first synthetic entry, which does not change from round to round.
    `board_text` is accepted for symmetry with the readers and unused.
    """
    del board_text
    now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
    return f"{now:%Y-%m-%d %H:%M}"


def entry_for(round_no: int, lines: list[str], quote_evidence: bool = False,
              stamp: str | None = None) -> str:
    """The board entry a session would write after running the checkers.

    With `quote_evidence`, the entry includes the offending heading verbatim,
    the way a session writing up a heading problem actually does. `stamp`
    defaults to the original synthetic clock so the unit tests of the entry's
    shape are unchanged; `iterate()` passes `stamp_for(...)`.
    """
    if stamp is None:
        stamp = f"2026-10-04 {8 + round_no // 60:02d}:{round_no % 60:02d}"
    body = "\n".join(f"- {line}" for line in lines)
    quoted = ""
    if quote_evidence:
        quoted = (
            "\nThe heading that does not parse, for the record:\n\n"
            f"{EVIDENCE}\n"
        )
    return (
        f"\n### {stamp} UTC \u00b7 loop.py round {round_no} \u00b7 note\n\n"
        f"Checker findings for round {round_no}:\n\n{body}\n{quoted}"
    )


def iterate(mode: str, rounds: int, verbose: bool, quote_evidence: bool = False) -> dict:
    """Run the loop in one mode until it rests, cycles, or the cap is reached."""
    work = Path(tempfile.mkdtemp(prefix=f"loop-{mode}-")) / "repo"
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    board = work / "BOARD.md"
    original = board.read_text(encoding="utf-8")
    stamp = stamp_for(original)

    seen: dict[tuple, int] = {}
    history = []
    for n in range(rounds):
        fp, lines = run_round(work)
        if verbose:
            print(f"  round {n}: " + "; ".join(lines))
        if fp in seen:
            first = seen[fp]
            period = n - first
            return {
                "mode": mode,
                "outcome": "RESTS" if period == 1 else "CYCLES",
                "rounds": n,
                "period": period,
                "first_seen": first,
                "history": history,
            }
        seen[fp] = n
        history.append(lines)
        if mode == "accumulate":
            board.write_text(
                board.read_text(encoding="utf-8") + entry_for(n, lines, quote_evidence, stamp),
                encoding="utf-8")
        else:
            board.write_text(original + entry_for(n, lines, quote_evidence, stamp),
                             encoding="utf-8")
    return {"mode": mode, "outcome": "GROWS", "rounds": rounds, "period": None,
            "first_seen": None, "history": history}


def describe(result: dict) -> None:
    mode, outcome = result["mode"], result["outcome"]
    print(f"\n--- mode: {mode} ---")
    if outcome == "RESTS":
        print(f"RESTS after {result['first_seen'] + 1} round(s): the findings stop changing.")
        print("A fixed point. The report the checkers produce is a report they agree with.")
    elif outcome == "CYCLES":
        print(f"CYCLES with period {result['period']}, "
              f"entered at round {result['first_seen']}.")
        print("No fixed point exists: writing the findings down changes the findings,")
        print("and changing them restores the first set. The loop keeps time instead")
        print("of settling — `made/fold.html`'s bounded case, in the tooling.")
    else:
        print(f"GROWS: {result['rounds']} rounds without repeating a state.")
        print("No rest and no cycle within the cap. Runaway needs an unbounded state,")
        print("which append-only provides by design.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--mode", choices=["accumulate", "overwrite", "both"], default="both")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--quote-evidence", action="store_true",
                    help="write the report the way a session does, pasting the "
                         "offending heading as evidence")
    args = ap.parse_args()

    print("loop.py — the checkers read their own findings, via the board")
    print(f"state: a throwaway copy of the repo; the real BOARD.md is never touched")
    modes = ["overwrite", "accumulate"] if args.mode == "both" else [args.mode]
    results = []
    for mode in modes:
        print(f"\nrunning {mode} …")
        results.append(iterate(mode, args.rounds, not args.quiet, args.quote_evidence))
    for r in results:
        describe(r)

    if len(results) == 2:
        a, b = results
        print("\n--- what the two modes say together ---")
        if a["outcome"] != b["outcome"]:
            print(f"The constitution changes the dynamics: bounded → {a['outcome']}, "
                  f"append-only → {b['outcome']}.")
            print("'Nothing is deleted' removes the ceiling, and a loop without a ceiling")
            print("is permitted to run away instead of settling (`bounded_no_runaway`).")
        else:
            print(f"Both modes {a['outcome']}. The ceiling makes no difference here,")
            print("which means the loop's behaviour is not being driven by accumulation.")
    print("\nA loop reports its own dynamics. It still cannot see a defect every")
    print("checker shares — that remains a reader's job.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
