"""
vary_floors_words.py — the labels and the words are floors too, executable.

The series so far:
    vary_floors.py            vary coordinates      -> some claims survive
    vary_floors_extended.py   vary the group        -> survivor set shrinks
    vary_floors_meta.py       vary the group-choice -> "no frame certifies frames"
    vary_floors_ground.py     vary the critics      -> "the question fixes G"; stop

The ground script claimed an exit from the regress and listed three floors it
was knowingly standing on. It missed two, and its exit has a crack in it.

  W1  THE LIST IS A FLOOR. Points arrive as a sequence. No script varied the
      permutation group S_n. 'handedness', 'chirality', 'topmost index' all
      die under relabeling. On the generic world, F5's proud "orientation =
      CW" was the handedness of a random traversal order -- a fact about the
      list, not the shape.
  W2  CANONICALIZING THE ORDER BRINGS THE COORDINATES BACK. Fix W1 by sorting
      the points? Sort by x: rotation-dependent again. Sort by angle about
      the centroid: survives everything -- because it is CCW by construction
      and has become E3's vacuous control. The honest order-free chirality is
      built from equivariant ingredients (centroid, farthest pair), flips
      under a mirror as it should -- and is undefined exactly on symmetric
      worlds, where a lucky sample of S_n hid the tie.
  W3  THE WORD DOES NOT FIX G. "Is it round?" In similarity geometry a sheared
      circle is not round. In affine geometry every ellipse is a circle. Two
      claims, both honestly called 'roundness', one per group; a shear floor
      kills one and spares the other. The English question did not fix G.
      The *formalized* question did -- and formalizing it WAS choosing G.
  W4  THE GROUND SCRIPT'S OWN DIAGONAL WASN'T. Its F5 table had 'roundness'
      surviving all four columns, because every group in the table was a
      subgroup of Sim(2). And F3's "Lipschitz ratio" was one directional
      derivative from one seed. Re-measured here over many directions.
  W5  WHERE THAT LEAVES THE EXIT. "The question fixes G" is right only after
      you replace the question with a group. So invariance analysis is a
      translation device -- from words to groups -- and the one floor it
      cannot vary is the agreement about which translation you meant.
      That floor is not geometric. It is two people talking.

Run: python3 vary_floors_words.py
"""

import math
import random

from vary_floors_extended import (
    WORLD, N_TRUE, rot, scale, translate, reflect_x, reflect_y, compose,
    verdicts_for, survives, centroid, radii_from, signed_area, _z,
    ROT_FLOORS, ORTHO_FLOORS, SCALE_FLOORS, ORIENT_FLOORS,
)
from vary_floors_ground import GENERIC, roundness_val, jitter

W = 78


def banner(title):
    print("=" * W)
    print(title)
    print("=" * W)


def status(d):
    return "SURVIVES" if len(d) == 1 else "floor-artifact"


def show(d, indent="                   "):
    for v, fl in sorted(d.items()):
        print(f"{indent}{v}   <- {', '.join(fl)}")


# ---------------------------------------------------------------------------
# relabelings: the permutation group S_n acting on the LIST, not the plane
# ---------------------------------------------------------------------------
def permute(seed):
    def f(pts):
        rng = random.Random(seed)
        idx = list(range(len(pts)))
        rng.shuffle(idx)
        return [pts[i] for i in idx]
    return f


def reverse(pts):
    return list(reversed(pts))


RELABEL_FLOORS = {
    "identity": lambda pts: pts,
    "reverse": reverse,
    "shuffle A": permute(1),
    "shuffle B": permute(2),
}


def list_verdicts(claim, world, list_floors):
    """Like verdicts_for, but floors act on the whole list rather than on points."""
    d = {}
    for fname, f in list_floors.items():
        d.setdefault(claim(f(world)), []).append(fname)
    return d


# ---- the claims under test (copied from ground/extended so names match) ----
def claim_handedness(pts):
    return "orientation = CCW" if signed_area(pts) > 0 else "orientation = CW"


def claim_chirality(pts):
    A = signed_area(pts)
    rs = radii_from(pts, centroid(pts))
    m = sum(rs) / len(rs)
    return f"normalized signed area = {_z(A / (m * m), 4):.4f}"


def claim_topmost_index(pts):
    return f"highest point is #{max(range(len(pts)), key=lambda i: pts[i][1])}"


def claim_roundness(pts):
    return f"roundness = {_z(roundness_val(pts)):.6f}"


def claim_count(pts):
    return f"count = {len(pts)}"


LIST_CLAIMS = {
    "handedness (sign only)": claim_handedness,
    "chirality (signed area)": claim_chirality,
    "topmost index": claim_topmost_index,
    "roundness": claim_roundness,
    "count": claim_count,
}


# ============================================================================
# W1  THE LIST IS A FLOOR
# ============================================================================
def w1_list_is_a_floor():
    banner("W1  THE LIST IS A FLOOR: nobody varied the permutation group")
    print("  Every script received the world as a Python list and every claim was")
    print("  free to read the order. Vary the order and nothing else:\n")
    for wname, world in [("perfect circle", WORLD), ("generic world", GENERIC)]:
        print(f"  --- {wname} ---")
        for cname, cl in LIST_CLAIMS.items():
            d = list_verdicts(cl, world, RELABEL_FLOORS)
            print(f"  [{status(d):>14}] {cname}")
            show(d)
        print()
    print("  -> 'handedness' was the ground script's showcase orientation invariant")
    print("     (F5: 'Is it drawn CCW?'). Reverse the list and it flips. Shuffle it")
    print("     and the 'chirality' of the generic world becomes the signed area of")
    print("     a random self-intersecting polygon. The ground script's 'CW' verdict")
    print("     for the generic world was a fact about random.shuffle, not geometry.")
    print("     The series tested invariance under G acting on the PLANE and never")
    print("     noticed that the data lived in G x S_n.")
    print()


# ============================================================================
# W2  CANONICALIZING THE ORDER BRINGS THE COORDINATES BACK
# ============================================================================
def sort_by_x(pts):
    return sorted(pts)


def order_by_angle(pts):
    cx, cy = centroid(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def claim_handedness_sorted(pts):
    return "orientation(sorted by x) = " + ("CCW" if signed_area(sort_by_x(pts)) > 0 else "CW")


def claim_handedness_angular(pts):
    return "orientation(ordered by angle) = " + ("CCW" if signed_area(order_by_angle(pts)) > 0 else "CW")


def set_handedness(pts):
    """Order-free chirality: sign of cross(a-c, b-c) for the two points farthest
    from the centroid. Built only from equivariant pieces, so it is invariant
    under rotation/scale/translation/permutation and flips under reflection."""
    c = centroid(pts)
    ranked = sorted(pts, key=lambda p: -math.hypot(p[0] - c[0], p[1] - c[1]))
    a, b = ranked[0], ranked[1]
    cross = (a[0] - c[0]) * (b[1] - c[1]) - (a[1] - c[1]) * (b[0] - c[0])
    return cross


def claim_set_handedness(pts):
    return "set-orientation = " + ("CCW" if set_handedness(pts) > 0 else "CW")


def w2_canonical_order():
    banner("W2  CANONICALIZING THE ORDER BRINGS THE COORDINATES BACK")
    print("  Obvious fix for W1: impose a canonical order before measuring.")
    print("  Three candidates, tested on the generic world under BOTH kinds of floor:")
    print("  relabelings (S_n) and plane rotations (G).\n")
    cands = [
        ("sort by x, then shoelace", claim_handedness_sorted),
        ("order by angle about centroid", claim_handedness_angular),
        ("two farthest points from centroid", claim_set_handedness),
    ]
    print(f"  {'canonicalization':<36}{'under S_n':<18}{'under rotations':<18}{'under a mirror'}")
    for name, cl in cands:
        d_perm = list_verdicts(cl, GENERIC, RELABEL_FLOORS)
        d_rot = verdicts_for(cl, GENERIC, ROT_FLOORS)
        d_ref = verdicts_for(cl, GENERIC, {"identity": lambda p: p, "reflect x": reflect_x})
        flips = "flips (chirality)" if len(d_ref) == 2 else "does NOT flip"
        print(f"  {name:<36}{status(d_perm):<18}{status(d_rot):<18}{flips}")
    print("\n  -> Row 1: sorting by x closes the permutation floor and re-opens the")
    print("     coordinate floor; lexicographic order is not rotation-equivariant.")
    print("     Row 2 looks perfect -- and is E3's vacuous control in a costume.")
    print("     Sorting by angle about the centroid produces a CCW polygon BY")
    print("     CONSTRUCTION, so the shoelace sign is always +. It survives S_n,")
    print("     rotations AND mirrors because it has stopped measuring anything.")
    print("     A chirality that does not flip under a mirror is not a chirality.")
    print("     Row 3 is the real one: equivariant ingredients (centroid, distance")
    print("     ranking) with a sign that does flip. E7, again.")
    print("\n  The catch, and it is the ground script's catch turned on itself.")
    print("  Row 3 asks 'which two points are farthest from the centroid?'. On the")
    rs = radii_from(WORLD, centroid(WORLD))
    print(f"  perfect circle all {N_TRUE} radii agree to {max(rs) - min(rs):.1e}: a tie, broken")
    print("  by float noise and list order. Watch which pair gets picked:\n")
    c = centroid(WORLD)
    for fname, f in RELABEL_FLOORS.items():
        pts = f(WORLD)
        ranked = sorted(pts, key=lambda p: -math.hypot(p[0] - c[0], p[1] - c[1]))
        ia, ib = WORLD.index(ranked[0]), WORLD.index(ranked[1])
        print(f"      {fname:<10} farthest pair = (#{ia:>2}, #{ib:>2})   set-orientation = "
              f"{'CCW' if set_handedness(pts) > 0 else 'CW'}")
    print("\n  Four relabelings, four different 'farthest pairs', and the sign came out")
    print("  the same each time -- by luck (the pair is noise, the sign is a coin).")
    print("  With a sample of 4 the test reads SURVIVES. Take a world with EXACT ties:\n")
    SQUARE = [(1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0)]
    d = list_verdicts(claim_set_handedness, SQUARE, RELABEL_FLOORS)
    print(f"  [{status(d):>14}] set-orientation on an exact square, under S_n")
    show(d)
    print("\n  -> The order-free chirality is undefined exactly on the symmetric worlds")
    print("     the series kept testing on. F2 said the circle was the worst test")
    print("     world because of fixed points; here it is the worst because of ties")
    print("     -- and it HID the tie behind a lucky sample, which is F1's lesson")
    print("     about samples, now about S_n. Same disease, third symptom.")
    print()


# ============================================================================
# W3  THE WORD DOES NOT FIX G
# ============================================================================
def shear(k):
    return lambda p: (p[0] + k * p[1], p[1])


def stretch(a, b):
    return lambda p: (a * p[0], b * p[1])


AFFINE_ONLY = {
    "identity": lambda p: p,
    "shear 0.7": shear(0.7),
    "stretch 2x,0.5y": stretch(2.0, 0.5),
    "shear+rot": compose(shear(-0.4), rot(math.radians(29))),
}


def whiten(pts):
    """Map the point cloud to unit covariance. Any W with W C W^T = I works,
    and they differ by an orthogonal matrix, which 'roundness' ignores."""
    cx, cy = centroid(pts)
    xs = [x - cx for x, _ in pts]
    ys = [y - cy for _, y in pts]
    n = len(pts)
    a = sum(x * x for x in xs) / n
    b = sum(x * y for x, y in zip(xs, ys)) / n
    d = sum(y * y for y in ys) / n
    l11 = math.sqrt(a)
    l21 = b / l11
    l22 = math.sqrt(max(d - l21 * l21, 1e-300))
    # inverse of the lower-triangular Cholesky factor
    i11, i21, i22 = 1 / l11, -l21 / (l11 * l22), 1 / l22
    return [(i11 * x, i21 * x + i22 * y) for x, y in zip(xs, ys)]


def claim_affine_roundness(pts):
    return f"affine roundness = {_z(roundness_val(whiten(pts))):.6f}"


def w3_word_does_not_fix_G():
    banner("W3  THE WORD DOES NOT FIX G: two 'roundness' claims, one English question")
    print("  Q: 'Is it round?'")
    print("    similarity geometry : a circle is round, an ellipse is not")
    print("    affine geometry     : every ellipse is the image of a circle, so it IS round")
    print("  Each geometry has an honest claim called 'roundness'. Floors: pure affine")
    print("  maps the series never used (shear, anisotropic stretch).\n")
    for wname, world in [("perfect circle", WORLD), ("generic world", GENERIC)]:
        print(f"  --- {wname} ---")
        for cname, cl in [("roundness (similarity)", claim_roundness),
                          ("roundness (affine, whitened)", claim_affine_roundness)]:
            d = verdicts_for(cl, world, AFFINE_ONLY)
            print(f"  [{status(d):>14}] {cname}")
            show(d)
        print()
    print("  -> Same word, two groups, opposite verdicts. The ground script's exit")
    print("     was 'the question fixes G'. It does not. 'Round' did not tell us")
    print("     whether a sheared circle counts. What fixed G was the moment we")
    print("     wrote the claim down -- i.e. picked which transformations to divide")
    print("     out. So: the FORMALIZED question fixes G, trivially, because")
    print("     formalizing a question about shape IS naming a group (Klein, still).")
    print("     The English question was a floor the ground script stood on while")
    print("     saying it had reached ground.")
    print("\n  Bonus, in the series' tradition: the affine claim is built from")
    print("  equivariant pieces (centroid, covariance) divided out -- E7 one more")
    print("  time. Covariance whitening is to the affine group what centroid-")
    print("  anchoring was to translations and mean-radius was to scaling.")
    print()


# ============================================================================
# W4  THE GROUND SCRIPT'S OWN DIAGONAL WASN'T; F3 WAS ONE DIRECTION
# ============================================================================
def w4_own_medicine():
    banner("W4  THE GROUND SCRIPT'S OWN DIAGONAL WASN'T, AND F3 WAS ONE DIRECTION")
    print("  F5 advertised 'four questions, four groups, a clean diagonal of")
    print("  survivors'. Its own printed table had 'roundness' SURVIVING in all")
    print("  four columns. Reason: every group in the table (isometry, orientation-")
    print("  preserving, fixed-up) is a subgroup of the similarity group, and by")
    print("  E5/Part B a similarity invariant survives every subgroup. The table")
    print("  could not have been diagonal. Here is a group that is NOT inside Sim(2):\n")
    d = verdicts_for(claim_roundness, GENERIC, AFFINE_ONLY)
    print(f"  [{status(d):>14}] roundness (similarity) under affine floors")
    print("  -> Now the roundness row has an 'artifact' in it. The ground script")
    print("     said F2's circle was 'chosen to make the claims come out true'; its")
    print("     own group menu was chosen from inside one group, and so could not")
    print("     make any similarity invariant come out false.\n")

    print("  F3 reported |d roundness|/eps = 0.440 for five values of eps and called")
    print("  it a Lipschitz ratio. Same seed each time means the same jitter")
    print("  DIRECTION scaled down: that is one directional derivative, not a")
    print("  Lipschitz constant. Over many directions (eps = 0.01):\n")
    r0 = roundness_val(WORLD)
    ratios = []
    for seed in range(400):
        w = jitter(WORLD, 0.01, seed=seed)
        ratios.append(abs(roundness_val(w) - r0) / 0.01)
    ratios.sort()
    n = len(ratios)
    print(f"      seeds: {n}   min {ratios[0]:.3f}   median {ratios[n//2]:.3f}   "
          f"max {ratios[-1]:.3f}   (F3's single value: 0.440)")
    print("\n  -> The conclusion (bounded, hence robust-as-continuity) stands. The")
    print("     evidence offered for it was a floor: one seed, presented as if it")
    print("     were a supremum. The spread is about 2x; the direction mattered.")
    print()


# ============================================================================
# W5  WHERE THAT LEAVES THE EXIT
# ============================================================================
def w5_exit():
    banner("W5  WHERE THAT LEAVES THE EXIT")
    print("  Tally, in the series' own currency -- floors each script stood on")
    print("  without varying:\n")
    rows = [
        ("vary_floors", "the world, G, the claim menu, rounding, the reference point"),
        ("extended",    "the sample of G, the symmetric world, string-equality robustness"),
        ("meta",        "non-closed 'groups', set theory dressed as group theory"),
        ("ground",      "the list order (S_n), the English question, one jitter direction,"),
        ("",            "a group menu drawn from inside one group"),
        ("THIS script", "GENERIC is still one draw; S_n sampled by two shuffles; 'affine"),
        ("",            "roundness' silently assumes nondegenerate covariance; whitening"),
        ("",            "by covariance is ONE affine canonicalization among many"),
    ]
    for tag, note in rows:
        print(f"  {tag:<12} {note}")
    print()
    print("  Every script found floors the previous one hid, including this one.")
    print("  That part of the meta script's thesis is confirmed, five times over.")
    print()
    print("  But look at WHAT KIND of floor each level found. The early ones were")
    print("  geometric (G, the world, the reference point) and could be varied in")
    print("  code. W3's floor is different in kind: it is the gap between the word")
    print("  'round' and a group. No transformation of the data varies it. You")
    print("  close it by saying 'I mean up to similarity' -- or by having a reader")
    print("  who already knows you do. Invariance analysis turns out to be a")
    print("  translation device from questions-in-words to groups, and the floor")
    print("  it cannot vary is the agreement about the translation.")
    print()
    print("  So the ground script's exit survives, amended:")
    print("      not  'the question fixes G'")
    print("      but  'stating G is the only precise way to state the question,")
    print("            and whether it is the question you meant is settled by")
    print("            people, not by the method.'")
    print()
    print("  That floor can be argued about. It cannot be varied. Stop here.")


if __name__ == "__main__":
    w1_list_is_a_floor()
    w2_canonical_order()
    w3_word_does_not_fix_G()
    w4_own_medicine()
    w5_exit()
