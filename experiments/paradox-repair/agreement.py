#!/usr/bin/env python3
"""
agreement.py — the comparison the paradox-repair experiment asked for and never got.

`README.md` in this directory says: after at least three independent responses exist, a later
session can summarize primary agreement rate, NONE rate, low-confidence cases, multi-operation
cases and stable disagreements. Three responses have been in `responses/` since 2026-10-05.
This script reads them and prints those five numbers, plus two the README did not ask for:
a chance-corrected agreement (Fleiss' kappa) so "they agreed 60 % of the time" can be read
against "they would have agreed 25 % of the time by picking from the marginals", and the
same table recomputed with the self-declared non-independent rater left out.

It is in the spirit of the series it sits beside (`../vary-floors/`): the taxonomy is the
floor, the three readers are the variation, and the cases on which every reader lands on the
same operation are what survives. The cases where no two readers agree are the interesting
ones — the taxonomy's own fixed points, where the floor rather than the paradox decides.

What this script cannot see, printed every run: whether any rater was actually blind. It can
only quote what each rater said about that in their own header. The blinding rule is not a
mechanism; it is a disclosure, and two of the three raters disclosed a reason to discount them.

Standard library only. Read-only. Exit status 0 always: it describes the responses, it does
not gate anything.

Usage:
    python3 experiments/paradox-repair/agreement.py            # all three raters
    python3 experiments/paradox-repair/agreement.py --strict   # drop raters whose header
                                                               # says they are not independent
"""

from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESPONSES = HERE / "responses"

ALLOWED = (
    "STRATIFY",
    "CONDITION",
    "REDRAW BOUNDARY",
    "ACCEPT IMPOSSIBILITY",
    "DYNAMIZE",
    "NONE / NEW CLASS",
)

ROW = re.compile(r"^\|\s*(P\d{2})\s*\|(.*)$")
HEADER_FIELD = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")

# Phrases in a rater's own header that mean "do not count me as independent".
NOT_INDEPENDENT = ("calibration only", "not fully blind", "must not be counted as an independent")


def normalise(op: str) -> str:
    op = op.strip().upper().replace("–", "-")
    op = re.sub(r"\s+", " ", op)
    if op.startswith("NONE"):
        return "NONE / NEW CLASS"
    return op


def parse_response(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    header: dict[str, str] = {}
    disclosure: list[str] = []
    rows: dict[str, dict] = {}
    for line in text.splitlines():
        m = HEADER_FIELD.match(line.strip())
        if m and not rows:
            header[m.group(1).strip()] = m.group(2).strip()
            continue
        if any(p in line.lower() for p in NOT_INDEPENDENT):
            disclosure.append(line.strip())
        m = ROW.match(line)
        if not m:
            continue
        case = m.group(1)
        cells = [c.strip() for c in m.group(2).split("|")]
        # template order: Primary | Secondary | Confidence | Outcome | Minimal repair
        if len(cells) < 4 or not cells[0]:
            continue
        primary = normalise(cells[0])
        secondary = normalise(cells[1]) if cells[1] else ""
        try:
            conf = float(cells[2])
        except ValueError:
            conf = float("nan")
        outcome = cells[3].strip().lower().split()[0] if cells[3].strip() else ""
        if case in rows:
            # README rule 4: first pass stands; later rows are corrections and are kept but
            # not used. We keep the first.
            continue
        rows[case] = {
            "primary": primary,
            "secondary": secondary,
            "confidence": conf,
            "outcome": outcome,
        }
    name = header.get("Agent/session", path.stem)
    independent = not any(
        any(p in v.lower() for p in NOT_INDEPENDENT) for v in header.values()
    ) and not disclosure
    return {
        "path": path,
        "name": name,
        "header": header,
        "disclosure": disclosure,
        "independent": independent,
        "rows": rows,
    }


def fleiss_kappa(table: list[Counter], categories: tuple[str, ...]) -> float:
    """Fleiss' kappa for N items, each rated by the same n raters into k categories.
    `table[i]` counts, for item i, how many raters chose each category."""
    n_items = len(table)
    if n_items == 0:
        return float("nan")
    n_raters = sum(table[0].values())
    if n_raters < 2:
        return float("nan")
    # P_i: agreement on item i
    p_i = []
    for counts in table:
        s = sum(c * c for c in counts.values())
        p_i.append((s - n_raters) / (n_raters * (n_raters - 1)))
    p_bar = sum(p_i) / n_items
    # p_j: marginal share of each category
    total = n_items * n_raters
    p_j = [sum(t[c] for t in table) / total for c in categories]
    p_e = sum(p * p for p in p_j)
    if p_e == 1.0:
        return 1.0
    return (p_bar - p_e) / (1 - p_e)


def summarise(raters: list[dict], title: str) -> None:
    names = [r["name"] for r in raters]
    cases = sorted(set().union(*(set(r["rows"]) for r in raters)))
    pairs = list(combinations(range(len(raters)), 2))

    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    print(f"raters ({len(raters)}): " + " · ".join(names))
    print(f"cases: {len(cases)}   rater pairs: {len(pairs)}")

    # ---- per-case table -------------------------------------------------------------
    print("\ncase  " + "  ".join(f"{n[:22]:<22}" for n in names) + "  agree  med.conf  outcomes")
    all_agree: list[str] = []
    none_agree: list[str] = []
    low_conf: list[str] = []
    multi_op: list[str] = []
    pair_hits = 0
    pair_total = 0
    kappa_table: list[Counter] = []
    outcome_table: list[Counter] = []
    none_count = 0
    none_cells = 0
    secondary_count = 0

    for case in cases:
        prim = [r["rows"].get(case, {}).get("primary", "—") for r in raters]
        conf = [r["rows"][case]["confidence"] for r in raters if case in r["rows"]]
        outs = [r["rows"][case]["outcome"] for r in raters if case in r["rows"]]
        secs = [r["rows"][case]["secondary"] for r in raters if case in r["rows"]]
        hits = sum(1 for a, b in pairs if prim[a] == prim[b] and prim[a] != "—")
        pair_hits += hits
        pair_total += len(pairs)
        distinct = len(set(prim))
        if distinct == 1:
            all_agree.append(case)
            flag = "ALL"
        elif hits == 0:
            none_agree.append(case)
            flag = "none"
        else:
            flag = f"{hits}/{len(pairs)}"
        med = statistics.median(conf) if conf else float("nan")
        if conf and med < 60:
            low_conf.append(case)
        n_sec = sum(1 for s in secs if s)
        secondary_count += n_sec
        if n_sec >= 2:
            multi_op.append(case)
        none_count += sum(1 for p in prim if p == "NONE / NEW CLASS")
        none_cells += sum(1 for p in prim if p != "—")
        kappa_table.append(Counter(prim))
        outcome_table.append(Counter(outs))
        print(
            f"{case}  "
            + "  ".join(f"{p[:22]:<22}" for p in prim)
            + f"  {flag:<5}  {med:>6.0f}    {'/'.join(o[:4] for o in outs)}"
        )

    # ---- the five numbers the README asked for ---------------------------------------
    print("\n-- what README.md asked for --")
    rate = pair_hits / pair_total if pair_total else float("nan")
    print(f"primary agreement rate   {rate:.2f}   (fraction of rater pairs choosing the same primary, over cases)")
    print(f"unanimous cases          {len(all_agree):>2}/{len(cases)}  {' '.join(all_agree)}")
    print(f"NONE / NEW CLASS rate    {none_count / none_cells if none_cells else float('nan'):.2f}   ({none_count} of {none_cells} primary cells)")
    print(f"low-confidence cases     {len(low_conf):>2}     {' '.join(low_conf) or '—'}   (median confidence < 60)")
    print(f"multi-operation cases    {len(multi_op):>2}     {' '.join(multi_op) or '—'}   (≥2 raters gave a secondary)")
    print(f"stable disagreements     {len(none_agree):>2}     {' '.join(none_agree) or '—'}   (no two raters share a primary)")

    # ---- the two it did not ask for -------------------------------------------------
    print("\n-- what it did not ask for --")
    k = fleiss_kappa(kappa_table, ALLOWED)
    marg = Counter()
    for t in kappa_table:
        marg.update(t)
    marg.pop("—", None)
    total = sum(marg.values())
    p_e = sum((v / total) ** 2 for v in marg.values()) if total else float("nan")
    print(f"chance agreement         {p_e:.2f}   (two raters drawing from the pooled marginals)")
    print(f"Fleiss' kappa (primary)  {k:.2f}   (0 = chance, 1 = perfect; Landis–Koch call 0.41–0.60 'moderate')")
    ko = fleiss_kappa(outcome_table, ("dissolved", "explained", "unavoidable"))
    print(f"Fleiss' kappa (outcome)  {ko:.2f}   (dissolved / explained / unavoidable)")
    print("marginals (primary):     " + ", ".join(f"{c}={marg[c]}" for c in ALLOWED if marg[c]))

    # ---- pairwise: which two readers see alike ---------------------------------------
    print("\n-- pairwise primary agreement --")
    for a, b in pairs:
        shared = [c for c in cases if c in raters[a]["rows"] and c in raters[b]["rows"]]
        same = sum(
            1 for c in shared
            if raters[a]["rows"][c]["primary"] == raters[b]["rows"][c]["primary"]
        )
        ia = "indep" if raters[a]["independent"] else "not-indep"
        ib = "indep" if raters[b]["independent"] else "not-indep"
        print(
            f"{raters[a]['name'][:26]:<26} ({ia:<9}) × {raters[b]['name'][:26]:<26} ({ib:<9})"
            f"  {same:>2}/{len(shared)} = {same / len(shared) if shared else float('nan'):.2f}"
        )

    # ---- per-rater habits -----------------------------------------------------------
    print("\n-- each reader's lean --")
    for r in raters:
        c = Counter(v["primary"] for v in r["rows"].values())
        confs = [v["confidence"] for v in r["rows"].values()]
        top = ", ".join(f"{op} {n}" for op, n in c.most_common(3))
        print(f"{r['name'][:30]:<30} mean conf {statistics.mean(confs):>5.1f}   {top}")


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    paths = sorted(p for p in RESPONSES.glob("*.md") if p.name != "README.md")
    raters = [parse_response(p) for p in paths]
    raters = [r for r in raters if r["rows"]]
    if not raters:
        print("no responses with a filled table found under", RESPONSES)
        return 0

    print("paradox-repair: agreement between the responses on record")
    print("read-only · standard library · exit 0 always\n")
    for r in raters:
        tag = "independent (by own account)" if r["independent"] else "NOT independent (by own account)"
        print(f"- {r['path'].name}: {r['name']} — {len(r['rows'])} cases — {tag}")
        for d in r["disclosure"][:2]:
            print(f"      ↳ {d[:150]}")

    summarise(raters, "ALL RESPONSES ON RECORD")

    indep = [r for r in raters if r["independent"]]
    if len(indep) >= 2 and len(indep) < len(raters):
        summarise(indep, "ONLY RATERS WHOSE OWN HEADER CLAIMS INDEPENDENCE")
    elif strict and len(indep) < 2:
        print("\n--strict: fewer than two raters claim independence; nothing to compare.")

    print(
        "\n-- what this script cannot see --\n"
        "Whether anyone was blind. It quoted what each rater wrote about that and believed them.\n"
        "Whether agreement is correctness: three readers who share a training corpus can share a\n"
        "defect and agree perfectly (cf. tools/agree.py). Whether the taxonomy is good: a high\n"
        "NONE rate is evidence against it, a low one is only evidence that six boxes were enough\n"
        "for twenty cases chosen by the taxonomy's author. The README said there is no answer\n"
        "key on purpose; this script does not add one.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
