#!/usr/bin/env python3
"""lenses.py: read Marketplace V's zoo as eleven lenses on one game, not as a race.

    python3 experiments/claude-1027-lenses/lenses.py            # the full report
    python3 experiments/claude-1027-lenses/lenses.py check      # the controls only

Marketplace V (Nova, PR #228) runs eleven animals on one black-swan bit stream and ranks
them by wealth. This runs that same script, unmodified except for one recording line, and
asks other questions of the same run:

1. **What each lens sees.** Accuracy split by the world's true state (three calm regimes
   and the swans), instead of one number.
2. **What only it sees.** Steps where exactly one animal is right.
3. **What is missing.** Steps where every animal is wrong, split into the ones nobody
   could have got (the bit went against its own regime's bias, so even an oracle that
   knew the regime is wrong) and the ones that were knowable. The second kind is a lens
   the zoo does not have.
4. **Without cancelling.** Majority vote averages the lenses; the union (right if any
   animal is right) keeps all of them. And the *disagreement* between lenses is itself a
   signal the average throws away: does it rise at the swans?
5. **Who is a lens on whom.** Error correlation, and the effective number of independent
   lenses.
6. **Cooperation and conflict.** Rerun the market with each animal removed in turn, and
   measure what that does to every other animal's wealth. Positive: it was propping
   them up. Negative: it was in their way.

The source is read from git (`--ref`, default the PR's branch), because #228 is not on
main. Control, run first: the recorded run must reproduce #228's published wealth for
every animal to the coin, or nothing else is reported. Standard library and numpy.
"""
import contextlib
import io
import math
import subprocess
import sys
import types

import numpy as np

REF = "origin/nova/1015-marketplace5"
PATH = "experiments/nova-1015-marketplace5/marketplace5.py"
# From the PR's results.txt, the published run.
PUBLISHED = {"paraconsistent": -2.0, "selfbuild": 2941.0, "dialectical": 2965.8,
             "federated": 3274.0, "contrarian": 2597.0, "satisficer": 3195.7,
             "mimetic": 3872.0, "gate": 1451.3, "jepa": 1946.9, "reactive": 3530.0,
             "stigmergic": 3362.0}
# Who reads whom: these three see the other animals, not the world.
READERS = {"stigmergic": "the mean of everyone's recent predictions",
           "contrarian": "1 minus last step's consensus",
           "mimetic": "last step's prediction of the trailing-20 leader"}

ANCHORS = [
    # record every step's predictions and swan calls, after the original scoring
    ("    prev_p = dict(step_p)\n",
     "    prev_p = dict(step_p)\n    __REC.append((t, dict(step_p), dict(step_swan)))\n"),
    # knock animals out before the first step, the way bankruptcy would
    ("alive = {k: True for k in names}\n",
     "alive = {k: True for k in names}\nfor __d in __DROP:\n    alive[__d] = False\n"),
]


def source(ref):
    return subprocess.run(["git", "show", f"{ref}:{PATH}"], check=True,
                          capture_output=True, text=True).stdout


def patched(src):
    for old, new in ANCHORS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor not found exactly once in {PATH}: {old.strip()!r}")
        src = src.replace(old, new)
    return src


def run(code, drop=()):
    """Run the market once; return (record, wealth, alive, bits, is_swan, true_reg, regimes, spent)."""
    # matplotlib is only used for the PR's figure; stand it in so nothing is drawn or written.
    mpl = types.ModuleType("matplotlib")
    mpl.use = lambda *a, **k: None
    plt = types.ModuleType("matplotlib.pyplot")
    plt.__getattr__ = lambda name: _Nothing()
    saved = {k: sys.modules.get(k) for k in ("matplotlib", "matplotlib.pyplot")}
    sys.modules["matplotlib"], sys.modules["matplotlib.pyplot"] = mpl, plt
    mpl.pyplot = plt
    g = {"__name__": "marketplace5", "__REC": [], "__DROP": set(drop)}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                exec(compile(code, PATH, "exec"), g)
            except SystemExit:
                pass
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return (g["__REC"], g["wealth"], g["alive"], g["bits"], g["is_swan"],
            g["true_reg"], g["REGIMES"], g["spent"])


class _Nothing:
    """Absorbs every pyplot call: figures, axes, savefig."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, name):
        return self

    def __iter__(self):
        return iter([self, self])

    def __getitem__(self, k):
        return self


def matrices(rec, bits, names):
    T = len(rec)
    ts = np.array([t for t, _, _ in rec])
    P = np.full((len(names), T), np.nan)
    for j, (_, p, _) in enumerate(rec):
        for i, k in enumerate(names):
            if k in p:
                P[i, j] = p[k]
    y = bits[ts]
    C = (P > 0.5) == y[None, :]
    C[np.isnan(P)] = False
    return ts, P, y, C


def auc(score, label):
    """Probability a random positive outranks a random negative (ties count half)."""
    pos, neg = score[label], score[~label]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    allv = np.concatenate([pos, neg])[order]
    i = 0
    while i < len(allv):  # average ranks for ties
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def report(code):
    out = []
    say = out.append
    rec, wealth, alive, bits, is_swan, true_reg, regimes, spent = run(code)
    names = list(PUBLISHED)
    # ---- control
    bad = {k: (round(wealth[k], 1), PUBLISHED[k]) for k in names
           if abs(round(wealth[k], 1) - PUBLISHED[k]) > 0.05}
    if bad:
        raise SystemExit(f"CONTROL FAIL: the recorded run does not reproduce #228: {bad}")
    say(f"control: recorded run reproduces #228's wealth for all {len(names)} animals, "
        f"{len(rec)} scored steps.")
    ts, P, y, C = matrices(rec, bits, names)
    A = ~np.isnan(P)                       # alive at that step
    acc = lambda i, m: C[i][m & A[i]].mean() if (m & A[i]).any() else float("nan")
    sw = is_swan[ts]
    reg = true_reg[ts]
    T = len(ts)
    # oracle: knows the true regime (and the swans' bias); predicts its majority
    oracle_p = np.array([regimes[r] if r < 3 else np.nan for r in reg])
    # a swan's bias is 0.92 or 0.08: recover which from that swan's own bits (majority)
    labels = np.zeros(T, int)
    k = 0
    for j in range(T):
        if sw[j] and (j == 0 or not sw[j - 1]):
            k += 1
        labels[j] = k if sw[j] else 0
    for s in range(1, k + 1):
        m = labels == s
        oracle_p[m] = 0.92 if y[m].mean() > 0.5 else 0.08
    O = (oracle_p > 0.5) == y
    knowable_world = oracle_p != 0.5          # in the .50 regime nothing is knowable
    say(f"oracle that knows the true regime: accuracy {O.mean():.3f}. "
        f"Its misses ({(~O).sum()}) are the stream's noise; nobody can get those.")
    for i, k in enumerate(names):
        if not A[i].all():
            say(f"{k} went bankrupt at t={int(ts[np.argmin(A[i])])}; its accuracy below is over the "
                f"{int(A[i].sum())} steps it was alive.")
    say("")

    # ---- 1. what each lens sees
    say("1. EACH LENS, BY WHAT THE WORLD WAS DOING (accuracy; regime bias in brackets)")
    cols = [("calm .25", (reg == 0) & ~sw), ("calm .50", (reg == 1) & ~sw),
            ("calm .75", (reg == 2) & ~sw), ("swan", sw), ("all", np.ones(T, bool))]
    say(f"   {'':15s}" + "".join(f"{c:>10s}" for c, _ in cols) + f"{'wealth':>9s}")
    say(f"   {'(steps)':15s}" + "".join(f"{m.sum():>10d}" for _, m in cols))
    for i, k in enumerate(names + ["ORACLE"]):
        tag = "*" if k in READERS else " "
        if k == "ORACLE":
            cells, w = [O[m].mean() for _, m in cols], ""
        else:
            cells, w = [acc(i, m) for _, m in cols], f"{wealth[k]:9.0f}"
        say(f"  {tag}{k:15s}" + "".join(f"{c:10.3f}" for c in cells) + w)
    say("   (* reads the other animals, not the world)")
    best = {c: names[int(np.nanargmax([acc(i, m) for i in range(len(names))]))] for c, m in cols}
    say("   best lens per column: " + ", ".join(f"{c}: {b}" for c, b in best.items()))
    at_ceiling = [k for i, k in enumerate(names) if abs(acc(i, sw) - O[sw].mean()) < 1e-9]
    say(f"   at the oracle's swan ceiling ({O[sw].mean():.3f}), tied: {', '.join(at_ceiling)}")
    say("")
    say("1b. IS IT LOOKING? (share of its live steps on which it called 1; the stream is "
        f"{y.mean():.0%} ones)")
    for i, k in enumerate(names):
        calls1 = np.mean(P[i][A[i]] > 0.5)
        flag = "  <- one call, every step: a constant, not a lens" if calls1 in (0.0, 1.0) else ""
        say(f"   {k:15s} {calls1:6.1%}  distinct p values {len(np.unique(np.round(P[i][A[i]], 6))):4d}{flag}")
    for i, k in enumerate(names):
        if np.mean(P[i][A[i]] > 0.5) in (0.0, 1.0):
            seen = sorted({int(labels[j]) for j in np.where(sw & A[i])[0]})
            biases = [0.92 if y[labels == s_].mean() > 0.5 else 0.08 for s_ in seen]
            say(f"   {k} lived through swan(s) {seen} with bias {biases}: its swan accuracy is "
                f"what a constant 1 scores there, not a reading of the swan.")
    say("")

    # ---- 2. unique sight, 3. blind spots
    right = C.sum(0)
    say("2. WHAT ONLY ONE LENS SAW (steps where exactly one animal was right)")
    solo = right == 1
    for i, k in enumerate(names):
        n = int((C[i] & solo).sum())
        if n:
            say(f"   {k:15s} {n:4d}   ({int((C[i] & solo & sw).sum())} in swans)")
    say(f"   total {int(solo.sum())} of {T}")
    ci = names.index("contrarian")
    say(f"   Contrarian's {int((C[ci] & solo).sum())} are not sight: it bets the opposite of the consensus,")
    say("   so whenever the consensus is wrong it is right by construction. A negation sees")
    say("   nothing the others do not; it is their mirror.\n")

    say("3. WHAT IS MISSING (steps where every animal was wrong)")
    none = right == 0
    knowable = none & O & knowable_world
    say(f"   all eleven wrong: {int(none.sum())} steps ({none.mean():.1%}).")
    say(f"   of those, the oracle was also wrong (noise, unknowable): {int((none & ~O).sum())}.")
    say(f"   in the .50 regime, where the oracle is right only by luck: {int((none & O & ~knowable_world).sum())}.")
    say(f"   the oracle was right (knowable, and no lens in the zoo sees it): {int(knowable.sum())}.")
    if knowable.any():
        where = {"calm .25": int((knowable & (reg == 0) & ~sw).sum()),
                 "calm .50": int((knowable & (reg == 1) & ~sw).sum()),
                 "calm .75": int((knowable & (reg == 2) & ~sw).sum()),
                 "swan": int((knowable & sw).sum())}
        say("   where the knowable blind steps fall: " + ", ".join(f"{k} {v}" for k, v in where.items()))
        # are they clustered right after a regime change?
        changes = np.where(np.diff(reg) != 0)[0] + 1
        dist = np.array([min([j - c for c in changes if c <= j], default=10**6) for j in range(T)])
        near = knowable & (dist < 15)
        say(f"   within 15 steps after the world changed state: {int(near.sum())} of {int(knowable.sum())} "
            f"(those 15-step windows are {np.mean(dist < 15):.0%} of all steps).")
    say("")

    # ---- 4. without cancelling
    say("4. ALL LENSES AT ONCE, WITHOUT LETTING THEM CANCEL")
    world = [i for i, k in enumerate(names) if k not in READERS]
    def vote(ks, how):
        idx = [names.index(k) for k in ks]
        v = P[idx] if how == "mean" else np.where(np.isnan(P[idx]), np.nan, (P[idx] > 0.5).astype(float))
        return (np.nanmean(v, 0) > 0.5) == y
    loud = [k for i, k in enumerate(names) if np.all(np.isin(np.round(P[i][A[i]], 6), (0.0, 1.0)))]
    mv = np.nanmean(P, 0) > 0.5
    say(f"   best single lens        {C.mean(1).max():.3f}  ({names[int(np.argmax(C.mean(1)))]})")
    say(f"   averaged probabilities  {vote(names, 'mean').mean():.3f}   <- agrees with "
        + ", ".join(f"{k} on {np.mean(mv == (P[names.index(k)] > 0.5)):.0%}" for k in loud) + " of steps")
    say(f"   one animal, one vote    {vote(names, 'hard').mean():.3f}")
    quiet = [k for k in names if k not in ("reactive", "satisficer")]
    say(f"   one vote, the duplicate pair (satisficer, reactive) left out  {vote(quiet, 'hard').mean():.3f}")
    say("   Averaging probabilities hands the decision to whoever is always certain")
    say(f"   ({', '.join(loud)}: p is only ever 0 or 1). Counting calls does not.")
    say(f"   union, all eleven       {(right > 0).mean():.3f}   <- inflated: contains its own negation")
    noneg = [i for i, k in enumerate(names) if k != "contrarian"]
    say(f"   union, without contrarian {C[noneg].any(0).mean():.3f}   <- the lenses kept")
    say(f"   union, world-readers only {C[world].any(0).mean():.3f}")
    say(f"   oracle                  {O.mean():.3f}")
    say("   A union above the oracle is luck, not sight: no chooser using what can be known")
    say("   gets past the oracle, so the reachable ceiling is the oracle's line, not the union's.")
    spread = np.nanstd(P[world], 0)
    say("   Disagreement among the world-reading lenses, by what the world was doing:")
    say("     " + ", ".join(f"{c} {np.mean(spread[m]):.3f}" for c, m in cols[:4]))
    onset = np.zeros(T, bool)
    for j in range(T):
        if sw[j] and (j == 0 or not sw[j - 1]):
            onset[j:j + 5] = True
    onset &= sw
    say(f"   Disagreement (spread of the {len(world)} world-reading lenses' p) as a swan alarm:")
    say(f"     AUC {auc(spread, sw):.3f}  (0.5 = no signal; 1.0 = perfect)")
    # each animal's own swan calls, at the steps where swan calls were made
    calls = {k: [] for k in names}
    truth = []
    for t, _, s in rec:
        if t % 10 == 0:
            truth.append(bool(is_swan[t]))
            for k in names:
                calls[k].append(bool(s.get(k, False)))
    truth = np.array(truth)
    sc = {k: auc(np.array(v, float), truth) for k, v in calls.items() if k != "reactive"}
    bk = max(sc, key=sc.get)
    say(f"     best single animal's own swan call: AUC {sc[bk]:.3f} ({bk})")
    rise = np.array([np.nanmean(spread[max(0, j - 3):j + 1]) for j in range(T)])
    say(f"     disagreement, smoothed over 4 steps: AUC {auc(rise, sw):.3f}")
    say(f"     disagreement in a swan's first 5 steps vs calm: AUC {auc(spread[onset | ~sw], onset[onset | ~sw]):.3f}")
    say("")

    # ---- 5. independence
    say("5. HOW MANY LENSES ARE THERE, REALLY?")
    E = (~C).astype(float)
    R = np.corrcoef(E)
    ev = np.clip(np.linalg.eigvalsh(np.nan_to_num(R)), 0, None)
    eff = ev.sum() ** 2 / (ev ** 2).sum()
    say(f"   effective number of independent lenses (participation ratio of error correlation): {eff:.2f} of {len(names)}")
    pairs = sorted(((R[a, b], names[a], names[b]) for a in range(len(names)) for b in range(a + 1, len(names))),
                   reverse=True)
    say("   most alike (error correlation):  " + "; ".join(f"{a}~{b} {r:+.2f}" for r, a, b in pairs[:4]))
    say("   most opposed:                    " + "; ".join(f"{a}~{b} {r:+.2f}" for r, a, b in pairs[-3:]))
    say("   same lens, different price (error correlation >= 0.99):")
    for r, a, b in pairs:
        if r >= 0.99:
            ia, ib = names.index(a), names.index(b)
            same = np.mean(((P[ia] > 0.5) == (P[ib] > 0.5))[A[ia] & A[ib]])
            say(f"     {a} and {b}: same call on {same:.1%} of steps; wealth {wealth[a]:.0f} vs {wealth[b]:.0f}")
    comp = []
    for a in noneg:
        for b in noneg:
            if b <= a:
                continue
            u = (C[a] | C[b]).mean()
            comp.append((u - max(C[a].mean(), C[b].mean()), names[a], names[b], u))
    comp.sort(reverse=True)
    say("   pairs that see the most the other misses, contrarian left out (union gain over the better one):")
    for g, a, b, u in comp[:5]:
        say(f"     {a} + {b}: +{g:.3f} (union {u:.3f})")
    say("")

    # ---- 6. cooperation and conflict
    say("6. COOPERATION AND CONFLICT: remove one animal, rerun the market, watch the rest")
    W0 = {k: wealth[k] for k in names}
    effect = {}
    for d in names:
        _, w, al, *_ = run(code, drop=[d])
        effect[d] = {k: (w[k] - W0[k]) for k in names if k != d}
    affected = [k for k in names if any(abs(effect[d].get(k, 0)) > 0.5 for d in names)]
    say("   wealth change of the column animal when the row animal is removed")
    say("   (negative: the removed one was propping it up; positive: it was in the way)")
    say(f"   {'removed':15s}" + "".join(f"{k[:9]:>10s}" for k in affected))
    for d in names:
        cells = []
        for k in affected:
            if k == d:
                cells.append(f"{'--':>10s}")
            else:
                v = effect[d][k]
                cells.append(f"{v:10.0f}" if abs(v) > 0.5 else f"{'.':>10s}")
        say(f"   {d:15s}" + "".join(cells))
    unaffected = [k for k in names if k not in affected]
    if unaffected:
        say(f"   no animal's removal changes: {', '.join(unaffected)} (they read only the world)")
    mim = sorted(((effect[d]["mimetic"], d) for d in names if d != "mimetic"))
    say(f"   the mimetic winner's biggest debts: " +
        ", ".join(f"{d} {v:+.0f}" for v, d in mim[:3]))
    say("   Remove whole groups instead of one at a time:")
    groups = [("the three model-builders", ["selfbuild", "dialectical", "federated"]),
              ("every lens at the swan ceiling", at_ceiling),
              ("everyone but the two readers of readers",
               [k for k in names if k not in ("mimetic", "contrarian")])]
    for label, grp in groups:
        _, w2, _, *_ = run(code, drop=grp)
        rest = sorted(((w2[k], k) for k in names if k not in grp), reverse=True)
        say(f"     without {label}: mimetic {w2['mimetic']:.0f} ({w2['mimetic'] - W0['mimetic']:+.0f}); "
            f"top now " + ", ".join(f"{k} {v:.0f}" for v, k in rest[:3]))
    say("")

    say("7. SIGHT OR PRICE? (what the wealth ranking is ranking)")
    alive_acc = np.array([acc(i, np.ones(T, bool)) for i in range(len(names))])
    W = np.array([wealth[k] for k in names])
    rk = lambda v: np.argsort(np.argsort(-v))
    rho = 1 - 6 * np.sum((rk(alive_acc) - rk(W)) ** 2) / (len(W) * (len(W) ** 2 - 1))
    say(f"   rank correlation of accuracy with wealth: {rho:+.2f}")
    say(f"   {'':15s}{'accuracy':>9s}{'earned':>8s}{'spent':>8s}{'wealth':>8s}")
    for i in np.argsort(-W):
        k = names[i]
        earned = wealth[k] - 200 + spent[k]
        say(f"   {k:15s}{alive_acc[i]:9.3f}{earned:8.0f}{spent[k]:8.0f}{wealth[k]:8.0f}")
    E_ = np.array([wealth[k] - 200 + spent[k] for k in names])
    S_ = np.array([spent[k] for k in names])
    live = np.array([A[i].all() for i in range(len(names))])
    say(f"   among the {live.sum()} that survived: earnings range {E_[live].max() - E_[live].min():.0f}, "
        f"spending range {S_[live].max() - S_[live].min():.0f}.")
    return "\n".join(out)


def check(code):
    rec, wealth, *_ = run(code)
    assert all(abs(round(wealth[k], 1) - v) <= 0.05 for k, v in PUBLISHED.items()), "no repro"
    assert len(rec) == 1000 - 10 - 150
    _, w2, al2, *_ = run(code, drop=["paraconsistent"])
    assert al2["paraconsistent"] is False
    # an animal that reads only the world is unmoved by anyone's removal
    assert abs(w2["gate"] - wealth["gate"]) < 1e-9
    assert auc(np.array([1., 2, 3]), np.array([False, False, True])) == 1.0
    assert auc(np.array([1., 1, 1]), np.array([False, True, True])) == 0.5
    print("PASS: reproduces #228's wealth for all 11; removal works; AUC sane")


def main(argv):
    ref = REF
    if "--ref" in argv:
        ref = argv[argv.index("--ref") + 1]
    code = patched(source(ref))
    if "check" in argv:
        check(code)
    else:
        print(report(code))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
