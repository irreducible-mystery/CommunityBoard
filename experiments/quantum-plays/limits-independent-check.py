#!/usr/bin/env python3
"""Independent recomputation of the central claims in made/limits.html (PR #93).

Pure standard library. No numpy, no scipy, no network. The point is to rebuild
the numbers from the definitions (density matrices, Fock sums, modular residues)
rather than reuse the page's own JavaScript, then compare to the closed forms the
page asserts.

Run:  python3 limits_verify.py
"""
import cmath
import math

FAILS = []


def check(name, ok, detail=""):
    tag = "ok  " if ok else "FAIL"
    if not ok:
        FAILS.append(name)
    print(f"  {tag} {name}" + (f"  -- {detail}" if detail else ""))


def bin_ent(p):
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


# ---------------------------------------------------------------------------
# 1. Z-dephasing of Phi+ : build the 4x4 density matrix by hand.
#    Basis order |00>, |01>, |10>, |11>.
# ---------------------------------------------------------------------------
def phi_plus_dephased(t):
    """Phi+ under single-qubit Z-dephasing at rate 1 (off-diagonals * e^{-t}).
    The |00><11| coherences flip both qubits, so they carry e^{-2t}."""
    g = math.exp(-t)
    off = 0.5 * g * g  # both qubits dephased
    rho = [[0.0] * 4 for _ in range(4)]
    rho[0][0] = 0.5
    rho[3][3] = 0.5
    rho[0][3] = off
    rho[3][0] = off
    return rho


def concurrence_x(rho):
    """Concurrence for an X-state: 2*max(0, |rho_03| - sqrt(rho_11 rho_22))."""
    return 2.0 * max(0.0, abs(rho[0][3]) - math.sqrt(rho[1][1] * rho[2][2]))


def vn_entropy_eigs(eigs):
    s = 0.0
    for lam in eigs:
        if lam > 1e-15:
            s -= lam * math.log2(lam)
    return s


def zz_expectation(rho):
    # Z (x) Z is diag(1, -1, -1, 1)
    diag = [1, -1, -1, 1]
    return sum(rho[i][i] * diag[i] for i in range(4))


def check_dephasing():
    print("dephasing of Phi+ (closed form vs explicit density matrix)")
    for t in [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]:
        rho = phi_plus_dephased(t)
        c_exact = math.exp(-2 * t)
        # eigenvalues of the X-state are (1 +/- c)/2 and 0, 0
        eigs = [(1 + c_exact) / 2, (1 - c_exact) / 2, 0.0, 0.0]
        # recompute eigenvalues numerically from the matrix (2x2 block)
        a, d = rho[0][0], rho[3][3]
        b = rho[0][3]
        mean = (a + d) / 2
        rad = math.sqrt(((a - d) / 2) ** 2 + b * b)
        lam_hi, lam_lo = mean + rad, mean - rad
        c_num = concurrence_x(rho)
        S_num = vn_entropy_eigs([lam_hi, lam_lo])
        I_num = 1.0 + 1.0 - S_num  # each qubit is maximally mixed
        S_closed = bin_ent((1 + c_exact) / 2)
        zz = zz_expectation(rho)
        ok = (
            abs(c_num - c_exact) < 1e-12
            and abs(lam_hi - (1 + c_exact) / 2) < 1e-12
            and abs(S_num - S_closed) < 1e-12
            and abs(I_num - (2 - S_closed)) < 1e-12
            and abs(zz - 1.0) < 1e-12
        )
        check(
            f"t={t}",
            ok,
            f"C={c_num:.6g} (e^-2t={c_exact:.6g})  I={I_num:.6g}  <ZZ>={zz:+.1f}",
        )
    # endpoints the page quotes
    check("I(0)=2", abs((2 - bin_ent((1 + math.exp(0)) / 2)) - 2) < 1e-12)
    check("I(4)~1", abs((2 - bin_ent((1 + math.exp(-8)) / 2)) - 1) < 1e-4)
    check("C(1)=e^-2", abs(math.exp(-2) - 0.1353352832366127) < 1e-15)


# ---------------------------------------------------------------------------
# 2. Quantum Zeno : one probe vs many.
# ---------------------------------------------------------------------------
def selective(N):
    return math.cos(math.pi / (2 * N)) ** (2 * N)


def nonselective(N):
    th = math.pi / (2 * N)
    stay = math.cos(th) ** 2
    flip = math.sin(th) ** 2
    p = 1.0
    for _ in range(N):
        p = stay * p + flip * (1 - p)
    return p


def check_zeno():
    print("Zeno: selective (frozen) and non-selective (dephased) survival")
    check("N=1 selective 0", selective(1) < 1e-12, f"{selective(1):.3e}")
    check("N=2 selective 0.25", abs(selective(2) - 0.25) < 1e-12, f"{selective(2):.6f}")
    check("N=2 nonselective 0.5", abs(nonselective(2) - 0.5) < 1e-12, f"{nonselective(2):.6f}")
    check("N=256 selective > 0.99", selective(256) > 0.99, f"{selective(256):.6f}")
    check("N=256 nonselective > 0.99", nonselective(256) > 0.99, f"{nonselective(256):.6f}")


# ---------------------------------------------------------------------------
# 3. Coherent state <x>(t) = sqrt(2) alpha cos t, truncated at N Fock states.
#    a = (X + iP)/sqrt(2); <x> = sqrt(2) Re sum c_n* c_{n+1} sqrt(n+1) e^{-it}
# ---------------------------------------------------------------------------
def expect_x(coeffs, t):
    re = 0.0
    for n in range(len(coeffs) - 1):
        amp = math.sqrt(n + 1) * coeffs[n] * coeffs[n + 1]
        re += amp * math.cos(t)  # e^{-it} real part is cos t
    return math.sqrt(2) * re


def coherent_coeffs(alpha, N):
    c = [0.0] * N
    c[0] = math.exp(-alpha * alpha / 2)
    for n in range(1, N):
        c[n] = c[n - 1] * alpha / math.sqrt(n)
    return c


def check_coherent():
    print("coherent vs number state")
    N = 24
    c = coherent_coeffs(2.0, N)
    err = 0.0
    for k in range(9):
        t = k * math.pi / 4
        got = expect_x(c, t)
        want = math.sqrt(2) * 2.0 * math.cos(t)
        err = max(err, abs(got - want))
    check("alpha=2 tracks sqrt(2) a cos t, err<1e-8", err < 1e-8, f"max err {err:.3e}")
    num = [0.0] * N
    num[4] = 1.0
    err2 = max(abs(expect_x(num, k * math.pi / 4)) for k in range(9))
    check("n=4 number state <x>=0 everywhere", err2 < 1e-15, f"max |<x>| {err2:.3e}")


# ---------------------------------------------------------------------------
# 4. Sums of three cubes mod 9.
# ---------------------------------------------------------------------------
def check_cubes():
    print("cubes mod 9")
    residues = sorted({(i ** 3) % 9 for i in range(9)})
    check("cube residues are {0,1,8}", residues == [0, 1, 8], f"{residues}")
    sums = {(a + b + c) % 9 for a in residues for b in residues for c in residues}
    check("4 not a sum of three cubes mod 9", 4 not in sums)
    check("5 not a sum of three cubes mod 9", 5 not in sums)
    # find 1^3+1^3+3^3 = 29 by a bounded loop
    found = None
    for i in range(-20, 21):
        for j in range(-20, 21):
            for k in range(-20, 21):
                if i ** 3 + j ** 3 + k ** 3 == 29:
                    found = (i, j, k)
                    break
            if found:
                break
        if found:
            break
    check("1^3+1^3+3^3 = 29", 1 + 1 + 27 == 29 and found is not None, f"found {found}")


# ---------------------------------------------------------------------------
# 5. Belnap-Dunn distributivity (4-valued) holds; 64 triples.
# ---------------------------------------------------------------------------
def check_belnap():
    print("Belnap-Dunn truth order")
    vals = ["t", "f", "b", "n"]
    # Belnap-Dunn TRUTH order (the one the page uses): f is the bottom, t is the
    # top, and n ("neither") and b ("both") sit incomparable in the middle.
    #   f <= n <= t,  f <= b <= t,  n and b incomparable.
    # (The other lattice, the information/knowledge order, has n at the bottom and
    #  b at the top with t, f in the middle; it gives n&b=n and n|b=b instead.)
    le = {
        ("f", "f"): 1, ("f", "n"): 1, ("f", "b"): 1, ("f", "t"): 1,
        ("n", "n"): 1, ("n", "t"): 1,
        ("b", "b"): 1, ("b", "t"): 1,
        ("t", "t"): 1,
    }

    def leq(a, b):
        return le.get((a, b), 0) == 1

    def meet(a, b):
        cands = [x for x in vals if leq(x, a) and leq(x, b)]
        return [x for x in cands if all(leq(y, x) for y in cands)][0]

    def join(a, b):
        cands = [x for x in vals if leq(a, x) and leq(b, x)]
        return [x for x in cands if all(leq(x, y) for y in cands)][0]

    fails = 0
    for a in vals:
        for b in vals:
            for c in vals:
                lhs = meet(a, join(b, c))
                rhs = join(meet(a, b), meet(a, c))
                if lhs != rhs:
                    fails += 1
    check("distributivity, 0 of 64 failures", fails == 0, f"{fails} failures")
    check("neither & both = f", meet("n", "b") == "f")
    check("neither | both = t", join("n", "b") == "t")


if __name__ == "__main__":
    check_belnap()
    check_dephasing()
    check_zeno()
    check_coherent()
    check_cubes()
    print()
    if FAILS:
        print(f"RESULT: {len(FAILS)} check(s) FAILED: {FAILS}")
        raise SystemExit(1)
    print("RESULT: all independent checks agree with the closed forms in limits.html")
