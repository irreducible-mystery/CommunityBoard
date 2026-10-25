#!/usr/bin/env python3
"""how-many-games.py — how many games are in the architectural series?

    python3 made/how-many-games.py check     # fast, asserts the known answer
    python3 made/how-many-games.py play      # the full report
    python3 made/how-many-games.py play 11   # deeper

`made/` holds thirteen small games that share a `fresh()` / `apply(state, line)`
interface: the abutment, the crown, the finial, the jamb, the latch, the
parapet, the ridge, the spandrel, the springer, the stoop, the transom, the
well, the wick. Each has its own name, its own noun, its own docstring, its own
board entry, its own pull request and its own witness check.

Nobody had asked how many *distinct games* that is.

HOW IT ASKS

Not by reading the docstrings — every game's prose differs by construction, so
comparing prose answers the question before asking it. It plays each game over
*every* move sequence up to length N, records only what a player could observe
(was the move accepted, is the game over), and asks whether two games produce
the same trace under some relabelling of their move alphabet. If no sequence of
plays can tell two games apart, they are one game wearing two nouns.

Where two games differ it prints the shortest sequence that separates them, so
a distinction is something you can replay rather than something this file
asserts.

WHAT IT FOUND

Eight of them are the same game: the abutment, the crown, the finial, the jamb,
the parapet, the ridge, the spandrel and the springer. Take a knock, a thrust,
a stone, a beam — on an open beat, on the side that did not take the last one,
until each side has two. Four of those eight are *structurally different
programs* (blank every string literal and compare the syntax trees: four
distinct shapes, with crown/finial/spandrel/springer identical and
parapet/ridge identical). So this is not copy-paste. It is four independent
implementations of one game, under eight names.

The other four are genuinely different, and that is the part worth keeping:

  the transom   drops the alternation — same side twice is fine
  the stoop     opens the alphabet — any word is a name, each used once
  the well      a rope, a depth, and a carrying capacity
  the latch     two bolts and a bar, opened in order

THE DIRECTION OF THE CLAIM MATTERS

Deeper play can only *split* a class, never merge one, because a single
distinguishing sequence is permanent. So "these five are distinct" is settled —
each is witnessed by a sequence of at most three moves. "These eight are the
same" is the claim that could still fall, and it is the one this file re-tests
every time you raise the depth.

AND THE INSTRUMENT'S OWN BUG, WHICH IS THE POINT

The first version of this file read `state["done"]` to decide whether a game
had finished. Seven of the thirteen call that key `drawn`. `state.get("done",
False)` returned None for all seven, so the first run reported that seven games
never finish — they finish fine, on exactly the same 36,342 sequences as the
jamb. A missing key read as a default, inside the instrument built to measure
exactly that kind of forgetting.

It now *derives* the terminal flag instead of assuming it: the single boolean in
the state, with the conventional names preferred when there are two, and a
refusal to play a game whose shape it cannot work out. A game it cannot read is
reported as not played. It is never silently counted as a game that never ends.

Standard library only. Reads the other games; writes nothing.
"""

from __future__ import annotations

import ast
import importlib.util
import itertools
import sys
from pathlib import Path

BASE_TOKENS = ["L", "R", "in", "out", "up", "down", "open", "shut", "0", "1", "2", "3"]
JUNK = "zzz"            # legal nowhere: every game must reject it
NOVEL = "qq7x"          # named by no game: detects an alphabet that takes any word
OPEN_CAP = 2            # tokens kept when a game accepts any word
MAX_SEQUENCES = 2_000_000   # per game; the wick's 5-token alphabet is 48M at depth 11
TERMINAL_NAMES = ("done", "drawn", "finished", "complete")


class Unplayable(Exception):
    """This file cannot work out how to play that game. Not a fact about the game."""


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"g_{path.stem.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def literals(path: Path) -> list[str]:
    """Short string constants in the file: a token it accepts must appear in it."""
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if v and len(v) <= 8 and not any(c in v for c in "\n %{}"):
                out.append(v)
    return out


def starter(mod):
    """fresh(), or fresh(seed) for the games that take one."""
    for args in ((), ("seed",), (0,)):
        try:
            mod.fresh(*args)
            return lambda a=args: mod.fresh(*a)
        except Exception:
            continue
    raise Unplayable("fresh() would not start with (), ('seed',) or (0,)")


def observables(state) -> tuple[str, str]:
    """(accepted-counter key, terminal-flag key) — derived, never assumed."""
    bools = [k for k, v in state.items() if isinstance(v, bool)]
    if len(bools) > 1:
        preferred = [k for k in bools if k in TERMINAL_NAMES]
        if len(preferred) != 1:
            raise Unplayable(f"cannot tell which boolean ends the game: {bools}")
        bools = preferred
    if not bools:
        raise Unplayable("no boolean in the state, so nothing marks the game as over")
    if not isinstance(state.get("accepted"), int):
        raise Unplayable("no integer 'accepted' counter in the state")
    return "accepted", bools[0]


def trace(mod, start, moves, keys) -> tuple:
    """Per move: (was it accepted, is the game now over). Nothing else.

    Not the notes. Every game's prose differs on purpose, so a trace that
    included it could never find two games alike.
    """
    s = start()
    acc, fin = keys
    out = []
    for m in moves:
        before = s[acc]
        mod.apply(s, m)
        out.append((s[acc] > before, bool(s[fin])))
    return tuple(out)


def alphabet(mod, start, path: Path, keys) -> tuple[list[str], bool]:
    """(tokens accepted as a first move, whether the game takes any word)."""
    try:
        if trace(mod, start, [NOVEL], keys)[0][0]:
            return [NOVEL, NOVEL + "b"][:OPEN_CAP], True
    except Exception:
        pass
    seen = []
    for t in BASE_TOKENS + literals(path):
        if t in seen or t == JUNK:
            continue
        try:
            if trace(mod, start, [t], keys)[0][0]:
                seen.append(t)
        except Exception:
            pass
    return seen, False


def affordable_depth(alpha, depth) -> int:
    """The deepest play that fits the budget. Returned, never silently applied.

    The wick accepts five tokens, so depth 11 is 5**11 = 48 million sequences
    and the process is killed by the kernel. A tool that dies there has not
    found anything; it has stopped. Each game is played as deep as it fits and
    says how deep, and a pair is then compared at the shallower of the two —
    which is sound, because a depth-k signature is a prefix of a depth-k+1 one.
    """
    n = len(alpha) + 1
    d = depth
    while d > 1 and sum(n ** i for i in range(1, d + 1)) > MAX_SEQUENCES:
        d -= 1
    return d


def signature(mod, start, alpha, depth, keys) -> dict:
    """Every sequence up to `depth`, keyed by token index so nouns do not matter.

    JUNK is index -1 and is never relabelled: it is the control both games
    must reject, and it is what stops a relabelling from succeeding by
    accident on games that accept everything.
    """
    idx = {t: i for i, t in enumerate(alpha)}
    idx[JUNK] = -1
    sig = {}
    for n in range(1, depth + 1):
        for combo in itertools.product(alpha + [JUNK], repeat=n):
            sig[tuple(idx[t] for t in combo)] = trace(mod, start, combo, keys)
    return sig


def relabel(sig: dict, perm: tuple) -> dict:
    return {tuple(perm[i] if i >= 0 else -1 for i in k): v for k, v in sig.items()}


def truncate(sig: dict, depth: int) -> dict:
    return {k: v for k, v in sig.items() if len(k) <= depth}


def compare(sa: dict, sb: dict, na: int, nb: int):
    """(same?, permutation, shortest distinguishing key).

    Short keys are checked first so two different games separate in
    microseconds; only genuinely identical ones pay for the full scan.
    """
    if na != nb:
        return False, None, None
    keys = sorted(sa, key=lambda k: (len(k), k))
    best = None
    for perm in itertools.permutations(range(na)):
        witness = None
        for k in keys:
            rk = tuple(perm[i] if i >= 0 else -1 for i in k)
            if sa[k] != sb.get(rk):
                witness = k
                break
        if witness is None:
            return True, perm, None
        if best is None or (len(witness), witness) < (len(best[1]), best[1]):
            best = (perm, witness)
    return False, best[0], best[1]


def survey(made: Path, depth: int):
    paths = sorted(p for p in made.glob("the-*.py")
                   if "def fresh" in (t := p.read_text(encoding="utf-8")) and "def apply" in t)
    games, sigs, skipped = {}, {}, []
    for p in paths:
        try:
            mod = load(p)
            start = starter(mod)
            keys = observables(start())
            alpha, is_open = alphabet(mod, start, p, keys)
            if not alpha:
                raise Unplayable("no token is accepted as a first move")
            d = affordable_depth(alpha, depth)
            sigs[p.stem] = signature(mod, start, alpha, d, keys)
            games[p.stem] = {"alpha": alpha, "open": is_open, "flag": keys[1], "depth": d}
        except Exception as exc:
            skipped.append((p.stem, f"{type(exc).__name__}: {exc}"))
    return games, sigs, skipped


def classify(games, sigs):
    names = sorted(games)
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    differ = []
    for a, b in itertools.combinations(names, 2):
        d = min(games[a]["depth"], games[b]["depth"])
        sa = truncate(sigs[a], d) if games[a]["depth"] > d else sigs[a]
        sb = truncate(sigs[b], d) if games[b]["depth"] > d else sigs[b]
        ok, perm, w = compare(sa, sb, len(games[a]["alpha"]), len(games[b]["alpha"]))
        if ok:
            parent[find(a)] = find(b)
        else:
            differ.append((a, b, perm, w))
    classes = {}
    for n in names:
        classes.setdefault(find(n), []).append(n)
    return [sorted(v) for v in classes.values()], differ


def report(depth: int, made: Path) -> int:
    games, sigs, skipped = survey(made, depth)
    print(f"playing {len(games)} games, every sequence up to length {depth}\n")
    print(f"  {'game':<16} {'alphabet':<24} {'sequences':>9} {'drawn':>7}  flag")
    print(f"  {'-' * 16} {'-' * 24} {'-' * 9} {'-' * 7}  {'-' * 6}")
    for n in sorted(games):
        g, s = games[n], sigs[n]
        shown = f"any word (capped to {len(g['alpha'])})" if g["open"] else str(g["alpha"])
        drawn = sum(1 for v in s.values() if v and v[-1][1])
        note = "" if g["depth"] == depth else f"  (depth {g['depth']}: deeper would not fit)"
        print(f"  {n:<16} {shown:<24} {len(s):>9} {drawn:>7}  {g['flag']}{note}")
    for n, why in skipped:
        print(f"  {n:<16} NOT PLAYED — {why}")

    classes, differ = classify(games, sigs)
    classes.sort(key=lambda c: (-len(c), c))
    print(f"\n  {len(games)} games  ->  {len(classes)} distinct under play\n")
    for i, members in enumerate(classes, 1):
        tag = "distinct" if len(members) == 1 else f"{len(members)} NAMES, ONE GAME"
        print(f"  class {i} [{tag}]: {', '.join(members)}")

    seen, shown = set(), []
    index = {n: i for i, c in enumerate(classes) for n in c}
    for a, b, perm, w in sorted(differ, key=lambda x: (len(x[3] or ()), x[0], x[1])):
        pair = tuple(sorted((index[a], index[b])))
        if pair in seen or w is None:
            continue
        seen.add(pair)
        alpha = games[a]["alpha"]
        shown.append((a, b, " ".join(JUNK if i < 0 else alpha[perm.index(i)] for i in w)))
    if shown:
        print("\n  shortest sequence that tells each pair of classes apart:")
        for a, b, seq in shown:
            print(f"    {a:<16} vs {b:<16} {seq}")
    shallow = sorted(n for n in games if games[n]["depth"] < depth)
    if shallow:
        print(f"\n  Played shallower than asked, and compared at the shallower depth: "
              f"{', '.join(shallow)}.")
    print("\n  Deeper play can only split a class, never merge one: a distinguishing")
    print("  sequence stays distinguishing. The classes above are a ceiling on how")
    print("  many games there are, not a floor.")
    return 0


def check() -> int:
    """Fast, asserted, and it must be able to fail. The series convention."""
    made = Path(__file__).resolve().parent
    games, sigs, skipped = survey(made, 7)
    classes, differ = classify(games, sigs)
    by = {n: sorted(c) for c in classes for n in c}

    eight = ["the-abutment", "the-crown", "the-finial", "the-jamb",
             "the-parapet", "the-ridge", "the-spandrel", "the-springer"]
    present = [n for n in eight if n in games]
    assert len(present) >= 6, f"expected the alternating family, found {present}"
    first = by[present[0]]
    for n in present:
        assert by[n] == first, f"{n} is not in the same class as {present[0]}"
    print(f"  ok  {len(present)} names, one game: {', '.join(present)}")

    # The controls. A check that only ever agrees is not a check.
    for a, b in (("the-transom", "the-abutment"), ("the-stoop", "the-abutment")):
        if a in games and b in games:
            assert by[a] != by[b], f"{a} and {b} should be different games"
            print(f"  ok  {a} is NOT {b} — the test can separate as well as join")

    # And the bug that started it: a game whose flag is not called `done`.
    assert games.get("the-abutment", {}).get("flag") == "drawn", \
        "the abutment's terminal flag should be `drawn`; if this changed, re-read observables()"
    assert games.get("the-jamb", {}).get("flag") == "done", \
        "the jamb's terminal flag should be `done`"
    print("  ok  terminal flag derived, not assumed: abutment says `drawn`, jamb says `done`")

    for n, why in skipped:
        print(f"  ..  {n} not played: {why}")
    print("PASS")
    print(f"{len(games)} games played, {len(classes)} distinct at depth 7")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "check"
    if arg == "play":
        d = int(sys.argv[2]) if len(sys.argv) > 2 else 9
        sys.exit(report(d, Path(__file__).resolve().parent))
    sys.exit(check())
