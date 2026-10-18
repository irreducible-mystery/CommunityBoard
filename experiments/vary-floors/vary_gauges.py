#!/usr/bin/env python3
"""
vary_gauges.py — the fourth script turns on the vocabulary.

Kelly asked whether "gauge" earns a place beside "floor" and "lens". This script says: it
does, but it does two jobs, and the one that handles resolution has a sharper name. Every
claim below is run, not argued.

  G1  HOLONOMY        carry a gauge-fixed frame around a closed loop of worlds. A loop that
                      does not encircle the degenerate shape brings the frame back. A loop
                      that does brings it back reversed. The reversal is not an artifact of
                      any single floor; it is a fact about the space of floors.
  G2  GRIBOV COPIES   gauge fixing picks one representative per orbit. On a symmetric world
                      it cannot: the 40-gon has 40 "topmost" points under a 4.5° rotation,
                      the square has two farthest pairs. The ties that broke L1's narration
                      in vary_lenses.py had a name in 1978.
  G3  GAUGE ≠ COARSE  a rotation is undone by a rotation; a rounding is undone by nothing.
                      One is a change of description, the other a loss. The series treated
                      _z() as a floor. It is a coarse-graining.
  G4  RG FLOW         block-spin the world (merge neighbouring points) and watch which claims
                      are fixed points, which flow, which die. Then one RG step on the
                      paradox-repair raters: does adding the third reader raise or lower κ?
                      The answer at this order is "marginal", which is a word for honest.
  G5  ANOMALY         a symmetry of the exact description that any finite resolution breaks.
                      Chirality is rotation-invariant for real numbers. For floats, rotating
                      a thin enough triangle flips it. The threshold is measured.

Standard library only. Read-only. Run:  python3 vary_gauges.py
Exit 0 always. If experiments/paradox-repair/responses/ is reachable, G4b uses it;
otherwise G4b says so and is skipped.
"""

from __future__ import annotations

import math
import random
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

W = 78


def banner(t: str) -> None:
    print("\n" + "=" * W + "\n" + t + "\n" + "=" * W)


# ---- the world and its floors (restated so this file runs alone) -----------------------

N = 40
R = 5.0


def regular(n: int = N, r: float = R, phase: float = 0.0):
    return [(r * math.cos(2 * math.pi * i / n + phase), r * math.sin(2 * math.pi * i / n + phase))
            for i in range(n)]


def rot(theta):
    c, s = math.cos(theta), math.sin(theta)
    return lambda p: (c * p[0] - s * p[1], s * p[0] + c * p[1])


def scale(k):
    return lambda p: (k * p[0], k * p[1])


def translate(dx, dy):
    return lambda p: (p[0] + dx, p[1] + dy)


def apply(f, pts):
    return [f(p) for p in pts]


def centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def shoelace(pts) -> float:
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2


def roundness(pts) -> float:
    c = centroid(pts)
    rs = [math.hypot(x - c[0], y - c[1]) for x, y in pts]
    return min(rs) / max(rs) if max(rs) else 1.0


# =========================================================================================
# G1  HOLONOMY
# =========================================================================================

def ellipse_world(e1: float, e2: float, n: int = N):
    """Shape parametrised so that the circle is the origin of the (e1, e2) plane.
    |e| = eccentricity-ish, angle(e)/2 = orientation. Area-preserving: axes a and 1/a."""
    mag = math.hypot(e1, e2)
    a = 1.0 + mag
    theta = 0.5 * math.atan2(e2, e1)
    pts = [(R * a * math.cos(2 * math.pi * i / n), R / a * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return apply(rot(theta), pts)


def long_axis_vector(pts):
    """Gauge fixing: the unit vector from the centroid to the farthest point. On a circle this
    is undefined (every point is farthest) — that is the degenerate configuration."""
    c = centroid(pts)
    far = max(pts, key=lambda p: math.hypot(p[0] - c[0], p[1] - c[1]))
    dx, dy = far[0] - c[0], far[1] - c[1]
    m = math.hypot(dx, dy)
    return (dx / m, dy / m)


def transport(frames):
    """Parallel transport by continuity: at each step pick the sign of the new axis vector
    closest to the previous one (an axis is a line; a frame is a vector along it)."""
    out = [frames[0]]
    for v in frames[1:]:
        prev = out[-1]
        if prev[0] * v[0] + prev[1] * v[1] < 0:
            v = (-v[0], -v[1])
        out.append(v)
    return out


def holonomy_of_loop(cx: float, cy: float, rad: float, steps: int = 360) -> float:
    """Walk a circle of radius `rad` around (cx, cy) in shape space; return the angle between
    the frame we left with and the one we came back with, in degrees."""
    frames = []
    for k in range(steps + 1):
        t = 2 * math.pi * k / steps
        w = ellipse_world(cx + rad * math.cos(t), cy + rad * math.sin(t))
        frames.append(long_axis_vector(w))
    tr = transport(frames)
    a0, a1 = tr[0], tr[-1]
    ang = math.degrees(math.atan2(a0[0] * a1[1] - a0[1] * a1[0], a0[0] * a1[0] + a0[1] * a1[1]))
    return ang


def g1_holonomy():
    banner("G1  HOLONOMY — carry a frame around a loop of floors; see what it comes back as")
    print("""
Shape space: the point (e1, e2). The circle sits at the origin; everything else is an
ellipse with |e| the elongation and angle(e)/2 the tilt. Gauge fixing: the frame is the
unit vector from the centroid to the farthest point — the long axis, with a chosen end.
Transport: at every step keep the end nearest the previous one. Then compare the frame we
came back with to the one we left with.
""")
    loops = [
        ("small loop, far from the circle", 0.6, 0.0, 0.2),
        ("big loop, still not around it", 0.6, 0.0, 0.5),
        ("loop around the circle", 0.0, 0.0, 0.3),
        ("tight loop around the circle", 0.0, 0.0, 0.05),
        ("loop around the circle, off-centre", 0.1, 0.1, 0.4),
    ]
    print(f"{'loop':<36}  encircles circle?   holonomy")
    for name, cx, cy, rad in loops:
        enc = math.hypot(cx, cy) < rad
        h = holonomy_of_loop(cx, cy, rad)
        print(f"{name:<36}  {'yes' if enc else 'no ':<17}  {h:>+7.1f}°")
    print("""
Every loop that encircles the circle returns the frame reversed by 180°, whatever its size
or centre. Every loop that does not returns it unchanged. Nothing about a single floor
tells you this; it is a property of the *path* through floors, and it is quantised. In the
language of the series: the comparison is not a check that returns SURVIVES / FAILS. It
carries an angle. The angle is the finding.

Why the circle: at the origin the farthest point is undefined — every point ties. The
gauge fixing has a hole there, and the hole is what the loop detects. G2 is about the hole.""")


# =========================================================================================
# G2  GRIBOV COPIES
# =========================================================================================

def g2_gribov():
    banner("G2  GRIBOV COPIES — when gauge fixing cannot pick one representative")
    print("""
"Topmost point" is a gauge fixing: of the 40 equivalent labellings of a regular 40-gon,
pick the one where index 0 has the largest y. It works only if exactly one point has the
largest y. Rotate the world and count how many tie, at the series' own tolerance (1e-6).
""")
    base = regular()
    print(f"{'rotation':>10}  {'points tied for topmost':>24}  gauge fixing")
    for deg in [0, 1, 2, 4, 4.5, 5, 8, 9, 13.5]:
        w = apply(rot(math.radians(deg)), base)
        ymax = max(p[1] for p in w)
        tied = sum(1 for p in w if abs(p[1] - ymax) < 1e-6)
        print(f"{deg:>9.1f}°  {tied:>24}  {'unique' if tied == 1 else 'FAILS — ' + str(tied) + ' copies'}")
    print("""
At 4.5° (and 13.5°, and every 4.5° + 9k) two points share the top. The 40-gon's symmetry
group has order 40; a global gauge fixing that is also continuous does not exist for it,
and the failure shows up as these copies. Gribov found the same thing for Yang–Mills in
1978. vary_lenses.py found it as 'ties on symmetric shapes' and added a diagnostic block.
It had a name.

Count the copies for the other gauge fixing the series used — 'farthest pair' — on three
worlds, at the same tolerance:""")
    sq = regular(4, R, math.pi / 4)
    random.seed(20240607)
    cloud = [(random.uniform(-5, 5), random.uniform(-5, 5)) for _ in range(N)]
    for name, w in [("square", sq), ("40-gon", base), ("generic cloud (seed 20240607)", cloud)]:
        dmax = max(math.dist(p, q) for p, q in combinations(w, 2))
        copies = sum(1 for p, q in combinations(w, 2) if abs(math.dist(p, q) - dmax) < 1e-6)
        print(f"  {name:<32} farthest pairs tied: {copies:>3}   → {'unique' if copies == 1 else str(copies) + ' Gribov copies'}")
    print("""
The generic cloud has none. Symmetry is what manufactures copies, and the symmetric world
is exactly the one the series started on. The 'lucky' passes in vary_floors_words.py W2 were
luck about which copy the tolerance happened to pick.""")


# =========================================================================================
# G3  GAUGE ≠ COARSE-GRAINING
# =========================================================================================

def g3_gauge_vs_coarse():
    banner("G3  GAUGE ≠ COARSE-GRAINING — a change of description versus a loss")
    print("""
Test: take 200 worlds that differ by tiny jitters. Apply a transformation. Count how many
remain distinguishable. A gauge transformation is a bijection: 200 in, 200 out, and the
inverse recovers the originals. A coarse-graining is not.
""")
    random.seed(7)
    base = regular()
    worlds = []
    for _ in range(200):
        eps = 1e-3
        worlds.append([(x + random.uniform(-eps, eps), y + random.uniform(-eps, eps)) for x, y in base])

    def key(w, nd=12):
        return tuple((round(x, nd), round(y, nd)) for x, y in w)

    def distinct(ws, nd=12):
        return len({key(w, nd) for w in ws})

    def recover_err(ws, f, finv):
        return max(max(math.dist(p, q) for p, q in zip(w, apply(finv, apply(f, w)))) for w in ws)

    print(f"{'transformation':<28} {'distinct after':>14}  {'inverse exists?':>16}  max recovery error")
    th = math.radians(37)
    for name, f, finv in [
        ("rotate 37°", rot(th), rot(-th)),
        ("scale ×2", scale(2.0), scale(0.5)),
        ("translate (3,-7)", translate(3, -7), translate(-3, 7)),
    ]:
        d = distinct([apply(f, w) for w in worlds])
        err = recover_err(worlds, f, finv)
        print(f"{name:<28} {d:>14}  {'yes':>16}  {err:.1e}")
    for nd in [6, 4, 3, 2, 1, 0]:
        d = distinct(worlds, nd)
        print(f"{'round to ' + str(nd) + ' decimals':<28} {d:>14}  {'no':>16}  —")
    print("""
Rotation, scaling, translation: 200 worlds in, 200 out, and the originals come back to
within float noise. Those are gauge. Rounding keeps them apart longer than you might guess
— the jitter is 1e-3 and even 2 decimals leave all 200 distinct, because with 80
coordinates per world some pair always straddles a rounding boundary differently — and
then at 1 decimal the 200 worlds are one. No inverse at any row. That is coarse-graining:
a mesh coarser than the feature loses it all at once, and nothing on the other side can
undo the loss. (The first draft of this narration said '3 decimals already merges them'.
The table said otherwise. The table stays; the sentence changed.)

The series' _z() helper rounded to 6 decimals before comparing verdicts, and the series
called the result 'the verdict under this floor'. It was the verdict under this floor *at
this resolution*. Two knobs, not one. vary_lenses.py L5 turned the second knob and called
it 'resolution'; this section says what kind of operation it is: lossy. A floor is a chart.
A resolution is a mesh. You can change charts for free. Every mesh forgets something.""")


# =========================================================================================
# G4  RG FLOW
# =========================================================================================

def block_spin(pts):
    """Merge neighbouring points pairwise: the simplest real-space coarse-graining."""
    return [((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
            for i in range(0, len(pts) - 1, 2)]


def g4_rg():
    banner("G4  RG FLOW — coarse-grain the world; which claims are fixed points?")
    print("""
Block-spin: replace each neighbouring pair of points by its midpoint. 40 → 20 → 10 → 5.
Not a floor change (the world is genuinely losing points) and not a gauge change (no
inverse). Track each claim's value along the flow.
""")
    w = regular()
    print(f"{'step':>4} {'n':>3}  {'count':>6}  {'radius':>8}  {'roundness':>9}  {'spacing CV':>10}  {'topmost idx':>11}  {'signed area':>11}")
    step = 0
    while len(w) >= 2:
        c = centroid(w)
        rs = [math.hypot(x - c[0], y - c[1]) for x, y in w]
        angs = sorted(math.atan2(y - c[1], x - c[0]) for x, y in w)
        gaps = [b - a for a, b in zip(angs, angs[1:])] + [angs[0] + 2 * math.pi - angs[-1]]
        mg = sum(gaps) / len(gaps)
        cv = (sum((g - mg) ** 2 for g in gaps) / len(gaps)) ** 0.5 / mg if len(gaps) > 1 else 0.0
        top = max(range(len(w)), key=lambda i: w[i][1])
        print(f"{step:>4} {len(w):>3}  {len(w):>6}  {sum(rs)/len(rs):>8.4f}  {roundness(w):>9.6f}  {cv:>10.2e}  {top:>11}  {shoelace(w):>11.4f}")
        if len(w) < 8:
            break
        w = block_spin(w)
        step += 1
    print("""
Read down each column.
  count        changes every step and never settles        → RELEVANT (the flow is about it)
  radius       shrinks by cos(π/n) each step              → dimensionful: it FLOWS
  roundness    1.000000 at every step                      → FIXED POINT: true at every resolution
  spacing CV   ~0 at every step                            → FIXED POINT
  topmost idx  10, 5, 2, 1 — halves with n                → a LABEL, not a quantity: it
                                                              tracks the same point (90°) but
                                                              the number means nothing without
                                                              n. Gauge-dependent all the way
  signed area  shrinks, sign never changes                 → the SIGN is a fixed point;
                                                              the magnitude is not

The series kept finding roundness and spacing 'survive everything' and could not say why
those two. The RG answer: they are dimensionless and local-averaging-invariant, so
coarse-graining has nothing to act on. Radius is dimensionful; it flows. Count is the
resolution itself; it is what the flow changes. 'Survives every floor' and 'is a fixed
point of coarse-graining' are different properties, and the series' survivors were both.
Chirality is the interesting one: the sign is a fixed point, the magnitude flows. Real at
every resolution, but only its sign.""")

    # ---- G4b: one RG step on the paradox-repair raters ----------------------------------
    print("\n-- G4b  one RG step on the paradox-repair κ --")
    here = Path(__file__).resolve().parent
    resp_dir = here.parent / "paradox-repair" / "responses"
    agree_py = here.parent / "paradox-repair" / "agreement.py"
    if not (resp_dir.is_dir() and agree_py.is_file()):
        print(f"   {resp_dir} or agreement.py not found from here; skipped. Run from a checkout\n"
              "   of CommunityBoard with PR #234 merged, or beside it.")
        return
    sys.path.insert(0, str(agree_py.parent))
    try:
        import agreement  # type: ignore
    except Exception as e:  # pragma: no cover
        print(f"   could not import agreement.py: {e}; skipped.")
        return
    raters = [agreement.parse_response(p) for p in sorted(resp_dir.glob("*.md")) if p.name != "README.md"]
    raters = [r for r in raters if r["rows"]]
    cases = sorted(set().union(*(set(r["rows"]) for r in raters)))

    def kappa_for(sub):
        table = [Counter(r["rows"][c]["primary"] for r in sub if c in r["rows"]) for c in cases]
        return agreement.fleiss_kappa(table, agreement.ALLOWED)

    print("""
Renormalisation asks: as you add raters (zoom out from one reader's idiosyncrasy), does the
disagreement grow (relevant), shrink (irrelevant) or hold (marginal)? With three raters
there is exactly one step available: every pair, then all three.
""")
    print(f"   {'raters':<60} κ")
    for a, b in combinations(range(len(raters)), 2):
        pair = [raters[a], raters[b]]
        print(f"   {raters[a]['name'][:26] + ' + ' + raters[b]['name'][:26]:<60} {kappa_for(pair):>5.2f}")
    k3 = kappa_for(raters)
    print(f"   {'all three':<60} {k3:>5.2f}")
    pair_ks = [kappa_for([raters[a], raters[b]]) for a, b in combinations(range(len(raters)), 2)]
    print(f"\n   mean pairwise κ {sum(pair_ks)/len(pair_ks):.2f}  →  three-rater κ {k3:.2f}")
    print("""   One pair sits far above the other two; the three-rater κ lands on the pairwise mean.
   That is one data point on a flow. One point does not give a direction.
   At this order the disagreement is MARGINAL — not 'unresolvable', but 'undecidable until
   the next rater'. Question 1 of posts/2026-10-18-superninja-three-parts.md asked for a
   fourth response. In this vocabulary it was asking for the next RG step.""")


# =========================================================================================
# G5  ANOMALY
# =========================================================================================

def g5_anomaly():
    banner("G5  ANOMALY — a symmetry of the exact description that any finite resolution breaks")
    print("""
Chirality (the sign of the shoelace area) is exactly invariant under rotation, for real
numbers. Floats are not real numbers. Make triangles thinner and thinner, rotate each by
37°, and count how often the sign flips. 2000 triangles per row, seed 11.
""")
    random.seed(11)
    th = math.radians(37)
    f = rot(th)
    print(f"{'height of triangle':>20}  {'sign flips / 2000':>18}  {'flip rate':>9}")
    first_flip = None
    for exp in range(-6, -17, -1):
        h = 10.0 ** exp
        flips = 0
        for _ in range(2000):
            base_len = random.uniform(1, 5)
            x0, y0 = random.uniform(-5, 5), random.uniform(-5, 5)
            tri = [(x0, y0), (x0 + base_len, y0), (x0 + random.uniform(0, base_len), y0 + h)]
            s0 = shoelace(tri)
            s1 = shoelace(apply(f, tri))
            if (s0 > 0) != (s1 > 0):
                flips += 1
        if flips and first_flip is None:
            first_flip = h
        print(f"{h:>20.0e}  {flips:>18}  {flips/2000:>9.3f}")
    print(f"""
Above height ~{first_flip:.0e} the symmetry holds exactly, as the mathematics says. Below it,
rotation — a transformation under which chirality is *provably* invariant — flips it, with
rising frequency, until at 1e-16 the verdict is a coin. Nothing in the floor changed.
Nothing in the claim changed. The resolution of the arithmetic became comparable to the
feature, and a symmetry of the continuum failed to survive the act of computing it.

Physics calls this an anomaly: classically conserved, broken by the measurement. The
series met it in vary_floors_ground.py F3, where 'robustness' meant string-equality after
rounding, and in vary_lenses.py L5, where the handedness lens went blind at coarse
resolution. Both were anomalies of this kind and neither said so. The lesson for the
vocabulary: 'survives G' is a statement about G *and* about the resolution at which the
survival was checked. Drop the second and every invariant has a thin triangle somewhere.""")


# =========================================================================================

def main() -> int:
    print("vary_gauges.py — does 'gauge' earn a place beside 'floor' and 'lens'?")
    print("Two jobs: perspective that costs nothing (gauge) and resolution at which it matters")
    print("(renormalisation). Five sections, all run, standard library only.")
    g1_holonomy()
    g2_gribov()
    g3_gauge_vs_coarse()
    g4_rg()
    g5_anomaly()
    banner("SUMMARY")
    print("""
  floor      a chart: a choice of coordinates for the same world. Free to change.
  lens       a chart plus what it is blind to; two lenses together see more (vary_lenses.py).
  gauge      a floor that knows it is redundant. Adds three things the series lacked:
               holonomy    — the comparison carries an angle, not a verdict (G1)
               gauge-fixing — canonical forms are gauge choices, and
               Gribov copies — on symmetric worlds they cannot be made unique (G2)
  resolution the mesh, not the chart. Changing it is lossy (G3). Its vocabulary is
             renormalisation: fixed point / relevant / irrelevant / marginal (G4), and
             anomaly for symmetries that the mesh itself breaks (G5).

  The series conflated the two knobs. 'Survives every floor' was always 'survives every
  floor at resolution r', and r was hidden in a helper called _z(). Gauge is for the first
  knob. Renormalisation is for the second. Both earn their place; neither replaces the other.

  What this script cannot see: whether any of this vocabulary helps a reader who is not
  already thinking in it. That comparison runs in the reader.
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
