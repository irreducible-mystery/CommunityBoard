#!/usr/bin/env python3
"""
Exhaustive verification of the (P2) case analysis in the Self-Strengthening Theorem.

Checks, for all (a, b) in N_0^2 with max(a, b) <= bound:
  1. Does the (R3)-at-n=4 constraint c = ab, d = a - b + b^2 give c, d >= 0?
  2. Is the resulting system actually power-associative at tau for n up to some N?
  3. What is mu(a, b)?
  4. Which products are zero (to test (R5) filtering)?
  5. Is the claimed minimizer (1, 0) actually the unique min under (R5)?
"""

from fractions import Fraction

def make_system(a, b):
    """Return the fusion multiplicities N as a dict keyed by (s1, s2, t)."""
    c = a * b
    d = a - b + b * b
    N = {
        ('t','t','t'): 1, ('t','t','g'): 1,
        ('t','g','t'): a, ('t','g','g'): b,
        ('g','t','t'): a, ('g','t','g'): b,  # commutativity P1
        ('g','g','t'): c, ('g','g','g'): d,
    }
    return N, c, d

def multiply(x, y, N):
    """Multiply two elements x, y given as dicts {basis: coeff}.
    Returns dict {basis: coeff}."""
    out = {'t': 0, 'g': 0}
    for s1, c1 in x.items():
        for s2, c2 in y.items():
            for t in ('t', 'g'):
                out[t] += c1 * c2 * N[(s1, s2, t)]
    return out

def eq(x, y):
    return x.get('t',0) == y.get('t',0) and x.get('g',0) == y.get('g',0)

def is_zero(x):
    return x.get('t',0) == 0 and x.get('g',0) == 0

def power_associative_at_tau(N, n_max=6):
    """Check that all parenthesizations of tau^n yield the same element, for n <= n_max."""
    tau = {'t': 1, 'g': 0}
    # Enumerate parenthesizations by recursion on trees.
    # For small n_max this is fine.
    def all_trees(n):
        if n == 1:
            return [tau]
        results = []
        for k in range(1, n):
            for left in all_trees(k):
                for right in all_trees(n - k):
                    results.append(multiply(left, right, N))
        return results
    for n in range(2, n_max + 1):
        trees = all_trees(n)
        if not trees:
            continue
        first = trees[0]
        for t in trees[1:]:
            if not eq(first, t):
                return False, n
    return True, None

def nondegenerate(N):
    """(R5): every pair (s1, s2) has nonzero product."""
    for s1 in ('t','g'):
        for s2 in ('t','g'):
            prod = {'t': N[(s1,s2,'t')], 'g': N[(s1,s2,'g')]}
            if is_zero(prod):
                return False
    return True

def mu(N):
    return sum(N.values())

def fully_associative(N):
    """Check (x*y)*z = x*(y*z) for all 8 triples in {t,g}^3."""
    basis = [{'t':1,'g':0}, {'t':0,'g':1}]
    names = ['t','g']
    for i in range(2):
        for j in range(2):
            for k in range(2):
                x, y, z = basis[i], basis[j], basis[k]
                lhs = multiply(multiply(x,y,N), z, N)
                rhs = multiply(x, multiply(y,z,N), N)
                if not eq(lhs, rhs):
                    return False, (names[i], names[j], names[k])
    return True, None

# Main exhaustive scan
print(f"{'(a,b)':>6} {'c=ab':>5} {'d':>4} {'mu':>4} {'R3@τ?':>6} {'R5?':>4} {'assoc?':>7} notes")
print("-" * 70)

bound = 4
candidates = []
for a in range(bound + 1):
    for b in range(bound + 1):
        N, c, d = make_system(a, b)
        if d < 0:
            continue  # not ℕ₀-valid
        pa, bad_n = power_associative_at_tau(N, n_max=6)
        nd = nondegenerate(N)
        fa, bad_triple = fully_associative(N)
        m = mu(N)
        candidates.append((a, b, c, d, m, pa, nd, fa))
        note = ""
        if (a,b) == (1,0): note = "<- Fibonacci"
        if (a,b) == (0,0): note = "<- absorbing-γ (the crack)"
        if (a,b) == (0,1): note = "<- projector-γ"
        print(f"({a},{b}) {c:>5} {d:>4} {m:>4} {str(pa):>6} {str(nd):>4} {str(fa):>7} {note}")

print()
print("=" * 70)
print("Filtering by (R1)-(R4) only (no R5):")
r14 = [c for c in candidates if c[5]]  # power-associative
r14.sort(key=lambda c: c[4])
print(f"  μ-min (no R5): (a,b)=({r14[0][0]},{r14[0][1]}) with μ={r14[0][4]}")

print()
print("Filtering by (R1)-(R5):")
r15 = [c for c in candidates if c[5] and c[6]]  # power-assoc AND nondegenerate
r15.sort(key=lambda c: c[4])
print(f"  μ-min (with R5): (a,b)=({r15[0][0]},{r15[0][1]}) with μ={r15[0][4]}")

print()
print("At the (R5)-filtered μ-min, is the system fully associative?")
a, b, c, d, m, pa, nd, fa = r15[0]
print(f"  (a,b)=({a},{b}): fully_associative = {fa}")

print()
print("Uniqueness check: all candidates with same minimum μ under (R5):")
min_mu = r15[0][4]
ties = [c for c in r15 if c[4] == min_mu]
print(f"  {len(ties)} candidate(s) at μ={min_mu}: {[(c[0],c[1]) for c in ties]}")