#!/usr/bin/env python3
"""PR #78 (The League): the last mover chooses the dice.

    git fetch origin ccr-611e5389-704ozy:pr78 && git worktree add /tmp/pr78 pr78
    python3 experiments/breaker/league78_probe.py /tmp/pr78

made/league.md says the round seed is the SHA-256 of every move file, "so no player can
predict them before the last move is committed". True for the first n-1 players. The last
player to commit can read everyone else's file on main and knows the referee, so they can
compute the seed for any file they might write, and their file has free bits: validate_move
treats an unknown key as "ignored", not fatal, so {"note": "3"} changes the seed and nothing
else. Below, merchant-4 in the demo match chooses whether round 1 has a disaster.

Read-only; nothing under games/ is touched.
"""
import copy
import json
import os
import random
import sys

PR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pr78"
if not os.path.exists(os.path.join(PR, "made", "market.py")):
    print(f"no made/market.py under {PR}; see the header")
    sys.exit(2)
sys.path.insert(0, os.path.join(PR, "made"))
import market  # noqa: E402

match_dir = os.path.join(PR, "games", "market", "000-demo")
rnd = 1
match = json.load(open(os.path.join(match_dir, "match.json"), encoding="utf-8"))
state = json.load(open(os.path.join(match_dir, "rounds", f"{rnd:03d}", "state.json"), encoding="utf-8"))
moves_dir = os.path.join(match_dir, "rounds", f"{rnd:03d}", "moves")
texts = {f[:-5]: open(os.path.join(moves_dir, f), encoding="utf-8").read() for f in sorted(os.listdir(moves_dir))}
me = sorted(texts)[-1]
mine = json.loads(texts[me])
p = match["rules"]["p_disaster"]
print(f"[league] match {match['seed']!r} round {rnd}; players {sorted(texts)}; I am the last to commit: {me!r}")


def first_draw(obj):
    mt = dict(texts)
    mt[me] = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    return random.Random(int(market.round_seed(match["seed"], rnd, mt), 16)).random()


u = first_draw(mine)
print(f"[league] my honest file gives the first draw u={u:.6f}; disaster if u < {p}: {'yes' if u < p else 'no'}")
for want, label in [(True, "a disaster"), (False, "no disaster")]:
    for i in range(10**6):
        m = copy.deepcopy(mine)
        m["note"] = str(i)
        u = first_draw(m)
        if (u < p) == want:
            clean, problems, fatal = market.validate_move(match, state, rnd, me, m)
            print(f"[league] {i + 1:>3} tries: note={m['note']!r} -> u={u:.6f}, {label}; referee: fatal={fatal}, problems={problems}")
            break
print("[league] the same holds for orbit.py and matrix.py: round_seed hashes the canonical text, and the")
print("         canonical text keeps every key the file had. A legal field would do too (a burn's 9th decimal).")
