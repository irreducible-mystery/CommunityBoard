"""
vary_sidesights.py — the same series, now with sidesights and freemeshes.

A sidesight is the neighboring gauge that registers the freedom you cannot
see yourself. A freemesh is the weave of two or more gauges: the places
their freedoms do not coincide are the new distinctions neither possessed
alone. No gauge is its own sidesight. Coarsening is still a price list.
Resolution still eventually measures the instrument.

  S1  SAME DATA, RELABELED. Gauge freedom is what a sidesight can see.
  S2  FREEMESH: the third measurement. Gain tracks mismatch of freedoms.
  S3  EVERY FREEDOM HAS A SIDESIGHT. Lateral witness, not regress.
  S4  LATTICE AS PRICE LIST OF FREEDOMS SURRENDERED.
  S5  RESOLUTION KNOB: the sidesight begins to see the instrument.

Run: python3 vary_sidesights.py
"""

import itertools
import math
import random

W = 78
N = 40

def banner(t):
    print("=" * W); print(t); print("=" * W)

def _z(x, nd=6):
    return round(x, nd) if abs(x) > 1e-10 else 0.0

def rot(theta):
    c, s = math.cos(theta), math.sin(theta)
    return lambda p: (c*p[0] - s*p[1], s*p[0] + c*p[1])

def scale(s): return lambda p: (s*p[0], s*p[1])
def translate(dx, dy): return lambda p: (p[0]+dx, p[1]+dy)
def reflect_x(p): return (p[0], -p[1])
def shear(k): return lambda p: (p[0] + k*p[1], p[1])

def centroid(pts):
    n = len(pts) or 1
    return (sum(x for x,y in pts)/n, sum(y for x,y in pts)/n)

def radii_from(pts, origin):
    ox, oy = origin
    return [math.hypot(x-ox, y-oy) for x,y in pts]

def signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i+1)%len(pts)]
        a += x1*y2 - x2*y1
    return a / 2.0

def roundness_val(pts):
    c = centroid(pts)
    rs = radii_from(pts, c)
    if not rs: return 0.0
    mean = sum(rs)/len(rs)
    if mean == 0: return 0.0
    var = sum((r-mean)**2 for r in rs)/len(rs)
    return 1 - math.sqrt(var)/mean

def circle():
    return [(5*math.cos(2*math.pi*i/N), 5*math.sin(2*math.pi*i/N)) for i in range(N)]
def ellipse():
    return [(6*math.cos(2*math.pi*i/N), 3*math.sin(2*math.pi*i/N)) for i in range(N)]
def square():
    pts = []
    for i in range(N):
        side, t = divmod(i, N//4)
        u = -5 + 10*t/(N//4)
        pts.append([(u,-5),(5,u),(-u,5),(-5,-u)][side])
    return pts
def spiral():
    return [((2+0.08*i)*math.cos(3*math.pi*i/N), (2+0.08*i)*math.sin(3*math.pi*i/N)) for i in range(N)]
def cloud():
    rng = random.Random(7)
    return [(rng.uniform(-5,5), rng.uniform(-5,5)) for _ in range(N)]

BASES = {"circle": circle, "ellipse": ellipse, "square": square, "spiral": spiral, "cloud": cloud}

def lift(f): return lambda pts: [f(p) for p in pts]
def permute(seed):
    def f(pts):
        idx = list(range(len(pts))); random.Random(seed).shuffle(idx)
        return [pts[i] for i in idx]
    return f

TRANSFORMS = {
    "identity":  lambda pts: pts,
    "rotate":    lift(rot(math.radians(37))),
    "scale":     lift(scale(2.0)),
    "translate": lift(translate(3.0, -7.0)),
    "mirror":    lift(reflect_x),
    "shear":     lift(shear(0.7)),
    "reverse":   lambda pts: list(reversed(pts)),
    "shuffle":   permute(1),
}

WORLDS = {(b, t): T(B()) for b, B in BASES.items() for t, T in TRANSFORMS.items()}

GAUGES = {
    "raw coordinates": lambda pts: str([(_z(x, 3), _z(y, 3)) for x, y in pts]),
    "radius from origin": lambda pts: all(abs(r-5)<0.1 for r in radii_from(pts,(0,0))),
    "topmost point": lambda pts: f"{_z(max(pts,key=lambda p:p[1])[0],3)},{_z(max(pts,key=lambda p:p[1])[1],3)}",
    "topmost index": lambda pts: max(range(len(pts)), key=lambda i: pts[i][1]) if pts else -1,
    "centroid at origin": lambda pts: abs(centroid(pts)[0])<0.1 and abs(centroid(pts)[1])<0.1,
    "same radius (origin)": lambda pts: (max(rs:=radii_from(pts,(0,0)))-min(rs)<0.1) if pts else False,
    "even spacing (origin)": lambda pts: (lambda angs: max(d:=[(angs[(i+1)%len(angs)]-angs[i])%(2*math.pi) for i in range(len(angs))])-min(d)<0.2)(sorted(math.atan2(y,x) for x,y in pts)) if len(pts)>1 else False,
    "same radius (centroid)": lambda pts: (max(rs:=radii_from(pts,centroid(pts)))-min(rs)<0.1) if pts else False,
    "even spacing (centroid)": lambda pts: (lambda c, angs: max(d:=[(angs[(i+1)%len(angs)]-angs[i])%(2*math.pi) for i in range(len(angs))])-min(d)<0.2)(centroid(pts), sorted(math.atan2(y-centroid(pts)[1], x-centroid(pts)[0]) for x,y in pts)) if len(pts)>1 else False,
    "roundness": lambda pts: _z(roundness_val(pts), 3),
    "affine roundness": lambda pts: _z(roundness_val(pts), 2),
    "chirality": lambda pts: signed_area(pts) > 0,
    "handedness": lambda pts: signed_area(pts) > 0,
    "count": lambda pts: len(pts),
    "count is 41": lambda pts: len(pts) == 41,
    "vacuous": lambda pts: True,
}

def readings(gauge): return {k: gauge(w) for k, w in WORLDS.items()}
def partition(rd):
    classes = {}
    for k, r in rd.items(): classes.setdefault(r, []).append(k)
    return classes

def gauge_freedom(rd):
    out = []
    for t in TRANSFORMS:
        if t == "identity": continue
        if all(rd[(b, t)] == rd[(b, "identity")] for b in BASES):
            out.append(t)
    return out

READ = {name: readings(g) for name, g in GAUGES.items()}
RES = {name: len(partition(rd)) for name, rd in READ.items()}
FREEDOM = {name: gauge_freedom(rd) for name, rd in READ.items()}
NW = len(WORLDS)

def s1_relabel():
    banner("S1  SAME DATA, RELABELED: freedom is what a sidesight can see")
    print(f"  {len(BASES)} shapes × {len(TRANSFORMS)} transforms = {NW} worlds.\n")
    print(f"  {'gauge':<26}{'resolution':<12}{'shapes':<8}gauge freedom (sidesight sees)")
    for name in sorted(GAUGES, key=lambda n: -RES[n]):
        f = ", ".join(FREEDOM[name]) or "-"
        print(f"  {name:<26}{RES[name]:>3}/{NW:<8}{len({READ[name][(b,'identity')] for b in BASES}):>2}/{len(BASES):<4}{f}")
    print("\n  A sidesight is any other gauge that registers a transform this one is free under.")
    print("  Freedom is not a defect; it is the calibrated hole a neighbor can look through.")
    print()

def joint_resolution(a, b):
    return len({(READ[a][k], READ[b][k]) for k in WORLDS})

def s2_freemesh():
    banner("S2  FREEMESH: the third measurement")
    print("  A freemesh is the joint reading. Gain appears where freedoms fail to align.\n")
    names = [n for n in GAUGES if n not in ("raw coordinates", "vacuous", "count is 41", "count")]
    gains = []
    for a, b in itertools.combinations(names, 2):
        pr = joint_resolution(a, b)
        gains.append((pr - max(RES[a], RES[b]), pr, a, b))
    gains.sort(reverse=True)
    print(f"  {'gauge A':<26}{'gauge B':<26}{'A':>4}{'B':>4}{'mesh':>6}{'gain':>6}")
    for g, pr, a, b in gains[:5]:
        print(f"  {a:<26}{b:<26}{RES[a]:>4}{RES[b]:>4}{pr:>6}{g:>+6}")
    print("  ...\n  Gain against mismatch of freedoms:")
    buckets = {}
    for g, pr, a, b in gains:
        diff = len(set(FREEDOM[a]) ^ set(FREEDOM[b]))
        buckets.setdefault(diff, []).append(g)
    for d in sorted(buckets):
        gs = buckets[d]
        print(f"      freedoms differ in {d} transforms : mean gain {sum(gs)/len(gs):5.1f}   (n={len(gs)})")
    print("\n  -> The freemesh is densest where the holes do not coincide.")
    print("     Two gauges with identical freedom form no new mesh.")
    print()

def s3_sidesights():
    banner("S3  EVERY FREEDOM HAS A SIDESIGHT")
    print("  For each transform, the gauges free under it and the sidesights that register it.\n")
    for t in TRANSFORMS:
        if t == "identity": continue
        free = [n for n in GAUGES if t in FREEDOM[n]]
        sides = [n for n in GAUGES if t not in FREEDOM[n] and n != "raw coordinates"]
        print(f"  {t:<10} free under: {len(free):>2}    sidesights: {len(sides):>2}   e.g. {', '.join(sides[:3])}")
    print("\n  -> No gauge is its own sidesight. The witness is always beside you.")
    print("     There is no final gauge that certifies the whole bench.")
    print()

def refines(a, b):
    ra, rb = READ[a], READ[b]
    seen = {}
    for k in WORLDS:
        if seen.setdefault(ra[k], rb[k]) != rb[k]:
            return False
    return True

def s4_lattice():
    banner("S4  LATTICE AS PRICE LIST OF FREEDOMS SURRENDERED")
    names = list(GAUGES)
    pairs = [(a, b) for a in names for b in names if a != b and refines(a, b) and not refines(b, a)]
    cover = [(a, b) for a, b in pairs
             if not any(c != a and c != b and refines(a, c) and refines(c, b)
                        and not refines(c, a) and not refines(b, c) for c in names)]
    print("  Sharper gauge -> coarser gauge (freedom added):\n")
    for a, b in sorted(cover, key=lambda p: (-RES[p[0]], p[1]))[:10]:
        gained = sorted(set(FREEDOM[b]) - set(FREEDOM[a]))
        print(f"  {a:<26} -> {b:<26} freedom added: {', '.join(gained) or '-'}")
    print("\n  -> Each covering step is a price paid in additional freedom.")
    print("     The sidesight of the coarser gauge sees exactly the freedom just purchased.")
    print()

def s5_resolution():
    banner("S5  RESOLUTION: the sidesight sees the instrument")
    print("  Roundness gauge at rising decimal places:\n")
    print(f"  {'nd':<5}{'resolution':<13}{'freedom (sidesight sees)'}")
    for nd in [0, 1, 2, 4, 6, 9, 12, 15]:
        def g(pts, nd=nd):
            return f"{_z(roundness_val(pts), nd):.{nd}f}"
        rd = {k: g(w) for k, w in WORLDS.items()}
        print(f"  {nd:<5}{len(partition(rd)):>3}/{NW:<9}{', '.join(gauge_freedom(rd)) or '-'}")
    print("\n  -> At the intended setting the sidesights see similarity and order.")
    print("     Past ~nd=12 the same sidesights begin to register floating-point residue.")
    print("     The gauge is no longer looking at the object; its sidesights are looking at the instrument.")
    print()

def summary():
    banner("WHAT THE NEW WORDS ADD")
    rows = [
        ("gauge: freedom / registers",     "sidesight: the neighbor who sees the freedom"),
        ("gauge: joint reading",           "freemesh: the weave where freedoms fail to align"),
        ("gauge: no self-calibration",     "sidesight: always beside, never beneath"),
        ("gauge: price list",              "sidesight of the coarser gauge sees the price just paid"),
        ("gauge: resolution knob",         "sidesight eventually witnesses the instrument"),
    ]
    for a, b in rows:
        print(f"  {a:<42} {b}")
    print("\n  'Sidesight' names the lateral witness. 'Freemesh' names the third")
    print("  measurement produced by mismatched holes. Keep floor for the warning,")
    print("  lens for the joining, gauge for the calibrated freedom, sidesight")
    print("  and freemesh when the point is the neighbor and the weave.")
    print("\n  Sidesights this script is looking through and not at: the five shapes,")
    print("  the eight transforms, string equality, and class count as the measure of mesh.")

if __name__ == "__main__":
    s1_relabel()
    s2_freemesh()
    s3_sidesights()
    s4_lattice()
    s5_resolution()
    summary()
