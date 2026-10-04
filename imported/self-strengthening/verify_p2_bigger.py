#!/usr/bin/env python3
"""Extend the scan and try to prove the 'all (a,b) give associative systems' claim analytically."""

import sympy as sp

a, b = sp.symbols('a b', integer=True, nonnegative=True)
c = a * b
d = a - b + b**2

# Symbolic fusion multiplicities
def N(s1, s2, t):
    table = {
        ('t','t','t'): 1, ('t','t','g'): 1,
        ('t','g','t'): a, ('t','g','g'): b,
        ('g','t','t'): a, ('g','t','g'): b,
        ('g','g','t'): c, ('g','g','g'): d,
    }
    return table[(s1,s2,t)]

def mul(x, y):
    """x, y are dicts {'t': coeff, 'g': coeff}."""
    out = {'t': 0, 'g': 0}
    for s1 in ('t','g'):
        for s2 in ('t','g'):
            for t in ('t','g'):
                out[t] += x[s1] * y[s2] * N(s1, s2, t)
    return {k: sp.expand(v) for k,v in out.items()}

def eq(x, y):
    return sp.simplify(x['t'] - y['t']) == 0 and sp.simplify(x['g'] - y['g']) == 0

basis = {
    't': {'t': 1, 'g': 0},
    'g': {'t': 0, 'g': 1},
}

print("Checking (x*y)*z = x*(y*z) symbolically for all 8 triples, assuming c=ab, d=a-b+b^2:")
print()
all_ok = True
for i in ('t','g'):
    for j in ('t','g'):
        for k in ('t','g'):
            x, y, z = basis[i], basis[j], basis[k]
            lhs = mul(mul(x,y), z)
            rhs = mul(x, mul(y,z))
            diff_t = sp.simplify(lhs['t'] - rhs['t'])
            diff_g = sp.simplify(lhs['g'] - rhs['g'])
            ok = (diff_t == 0 and diff_g == 0)
            all_ok = all_ok and ok
            status = "OK" if ok else "FAIL"
            print(f"  ({i},{j},{k}): {status}    lhs-rhs = ({diff_t}, {diff_g})")

print()
print(f"Overall: all 8 triples associative symbolically = {all_ok}")