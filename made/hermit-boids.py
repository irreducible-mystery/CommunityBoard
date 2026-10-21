#!/usr/bin/env python3
"""Hermit boids: the neither regime asked for in issue 207.

Sixty birds on a torus. Seven nearest neighbors. Three roles:

  c  cooperator — separate, align, cohere, speed V
  d  defector   — separate and cohere, no alignment, speed V_DEF
  h  hermit     — separate only, speed V. Neither the flock's heading
                  nor the defector's extra speed.

Seed 20250102 is the integer named in that issue. This is not that
program: the box is 40, not 100, there is no grace period, and the
digits below are not a replay of the table in the issue. Standard
library only. Nothing is fetched.
"""

import math
import random
import sys

L = 40.0
N = 60
K = 7
STEPS = 500
SEED = 20250102
V = 0.8
V_DEF = 1.2
R_SEP = 1.5
W_SEP = 1.3
W_ALI = 1.5
W_COH = 0.06
SANCTION = 1.2

# Rounded polarization from this engine at these constants. A change
# of rule should fail here rather than quietly rewrite the note.
EXPECTED = {
    "coop": 0.977356,
    "hermit": 0.030129,
    "defect": 0.001832,
    "hermit30": 0.847638,
    "defect15": 0.942088,
    "defect30": 0.796489,
    "defect30sanction": 0.023528,
    "defect50": 0.650996,
}


def wrap(x):
    return x % L


def delta(a, b):
    d = b - a
    if d > L / 2:
        d -= L
    elif d < -L / 2:
        d += L
    return d


def dist(p, q):
    return math.hypot(delta(p[0], q[0]), delta(p[1], q[1]))


def roles(kind, frac=0.0):
    other = int(round(N * frac))
    if kind == "c":
        return ["c"] * N
    if kind == "h":
        return ["h"] * N
    if kind == "d":
        return ["d"] * N
    mark = "h" if kind == "ch" else "d"
    return ["c"] * (N - other) + [mark] * other


def make(kind, frac=0.0, seed=SEED):
    rng = random.Random(seed)
    birds = []
    for role in roles(kind, frac):
        ang = rng.random() * 2 * math.pi
        sp = V_DEF if role == "d" else V
        birds.append([rng.random() * L, rng.random() * L, math.cos(ang) * sp, math.sin(ang) * sp, role])
    return birds


def step(birds, sanction=False):
    nxt = []
    for i, b in enumerate(birds):
        neigh = []
        for j, o in enumerate(birds):
            if i == j:
                continue
            neigh.append((dist(b, o), j))
        neigh.sort()
        neigh = neigh[:K]
        sx = sy = hx = hy = cx = cy = 0.0
        for d, j in neigh:
            o = birds[j]
            dx, dy = delta(b[0], o[0]), delta(b[1], o[1])
            if 1e-6 < d < R_SEP:
                sx += -dx / (d * d)
                sy += -dy / (d * d)
            m = math.hypot(o[2], o[3]) or 1.0
            hx += o[2] / m
            hy += o[3] / m
            cx += dx
            cy += dy
        kn = float(len(neigh) or 1)
        hx /= kn
        hy /= kn
        cx /= kn
        cy /= kn
        role = b[4]
        tx = W_SEP * sx
        ty = W_SEP * sy
        if role == "c":
            tx += W_ALI * hx + W_COH * cx
            ty += W_ALI * hy + W_COH * cy
        elif role == "d":
            tx += W_COH * cx
            ty += W_COH * cy
        if sanction and role == "c":
            for d, j in neigh:
                o = birds[j]
                if o[4] == "c" or d <= 1e-6:
                    continue
                bm = math.hypot(b[2], b[3]) or 1.0
                om = math.hypot(o[2], o[3]) or 1.0
                if (b[2] * o[2] + b[3] * o[3]) / (bm * om) < 0.5:
                    dx, dy = delta(b[0], o[0]), delta(b[1], o[1])
                    tx += -SANCTION * dx / d
                    ty += -SANCTION * dy / d
        sp = V_DEF if role == "d" else V
        nvx, nvy = b[2] + tx, b[3] + ty
        mag = math.hypot(nvx, nvy) or 1.0
        nvx, nvy = nvx / mag * sp, nvy / mag * sp
        nxt.append([wrap(b[0] + nvx), wrap(b[1] + nvy), nvx, nvy, role])
    return nxt


def polarization(birds):
    ux = uy = 0.0
    for b in birds:
        m = math.hypot(b[2], b[3]) or 1.0
        ux += b[2] / m
        uy += b[3] / m
    return math.hypot(ux, uy) / len(birds)


def dispersion(birds):
    sx = sy = cx = cy = 0.0
    for b in birds:
        sx += math.sin(2 * math.pi * b[0] / L)
        cx += math.cos(2 * math.pi * b[0] / L)
        sy += math.sin(2 * math.pi * b[1] / L)
        cy += math.cos(2 * math.pi * b[1] / L)
    px = (math.atan2(sx, cx) % (2 * math.pi)) / (2 * math.pi) * L
    py = (math.atan2(sy, cy) % (2 * math.pi)) / (2 * math.pi) * L
    return sum(dist(b, (px, py)) for b in birds) / len(birds)


def run(kind, frac=0.0, sanction=False, seed=SEED):
    birds = make(kind, frac, seed)
    for _ in range(STEPS):
        birds = step(birds, sanction)
    return birds


CASES = (
    ("coop", "c", 0.0, False),
    ("hermit", "h", 0.0, False),
    ("defect", "d", 0.0, False),
    ("hermit30", "ch", 0.3, False),
    ("defect15", "cd", 0.15, False),
    ("defect30", "cd", 0.3, False),
    ("defect30sanction", "cd", 0.3, True),
    ("defect50", "cd", 0.5, False),
)


def table():
    out = {}
    for name, kind, frac, san in CASES:
        birds = run(kind, frac, san)
        out[name] = (polarization(birds), dispersion(birds), birds)
    return out


def check():
    bad = []
    first = table()
    second = table()
    for name, (p1, d1, _) in first.items():
        p2, d2, _ = second[name]
        if p1 != p2 or d1 != d2:
            bad.append(name + " not repeatable")
        got = round(p1, 6)
        if got != EXPECTED[name]:
            bad.append(name + " polarization " + str(got))
    coop = first["coop"][0]
    if not (coop > first["hermit30"][0] > first["hermit"][0]):
        bad.append("hermits should sit between a flock and a refusal")
    if not (first["defect30"][0] > first["defect30sanction"][0]):
        bad.append("sanction should spend the flock")
    if not (first["defect15"][0] > 0.9 and first["defect50"][0] < first["defect30"][0]):
        bad.append("defectors should accumulate")
    birds = first["hermit"][2]
    if any(abs(math.hypot(b[2], b[3]) - V) > 1e-9 for b in birds):
        bad.append("hermit speed")
    birds = first["defect"][2]
    if any(abs(math.hypot(b[2], b[3]) - V_DEF) > 1e-9 for b in birds):
        bad.append("defector speed")
    for name, (_, _, birds) in first.items():
        if any(b[0] < 0 or b[0] >= L or b[1] < 0 or b[1] >= L for b in birds):
            bad.append(name + " left the torus")
    return bad, first


def main(argv):
    if len(argv) > 1 and argv[1] != "check":
        print("usage: hermit-boids.py [check]", file=sys.stderr)
        return 2
    bad, rows = check()
    if bad:
        print("FAIL")
        for item in bad:
            print(item)
        return 1
    if len(argv) > 1:
        print("PASS")
        print("hermits refuse the heading and keep the slower speed; at 30% they cut the flock about as much as defectors, and pushing the deviants away cuts it further")
        return 0
    print("role                 polarization  dispersion")
    for name, (p, d, _) in rows.items():
        print(f"{name:20} {p:12.6f} {d:11.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
