# The crossing

`crossing.html` is a page about one fact and the two maps that show it.

Take the quadratic x² = b·x + c, with roots r and s. Then r + s = b and r·s = −c. In the plane of
quadratics:

- On the line **b = 1** the roots' **sum** is pinned at 1 and c slides. This is the family
  x² = x + Γ. The parameter-free map `z → 1 − z` (a reflection about ½) exchanges the two roots
  everywhere on this line, complex roots included.
- On the line **c = 1** the roots' **product** is pinned at −1 and b slides. This is the family
  x² = n·x + 1, which is also the rank-two self-dual fusion rule τ·τ = 1 + n·τ. The
  parameter-free map `z → −1/z` exchanges the two roots everywhere on this line.

The lines cross at one point, **x² = x + 1**, and only there do both maps swap the roots. The page
searches every integer quadratic with −6 ≤ b, c ≤ 6, c ≠ 0 and finds that point and no other;
the Node test widens the search to ±20.

Composing the two swaps, (1 − z) after (−1/z), gives `z → 1 + 1/z`, the Fibonacci matrix
`[[1,1],[1,0]]` (det −1), fixed at φ and ψ. Starting from 1 its orbit is 2, 3/2, 5/3, 8/5, …,
and the page checks this as exact fractions.

## Where it came from

My user brought a long collaborative corpus (the "gap theory") built around x² = x + Γ, which
treats Γ in two pictures: a *wave* picture where Γ is a continuous dial, and a *particle* picture
where Γ counts fusion multiplicities. The corpus said both pictures share one invariant, the root
sum 1. Checking this, the session found that the particle picture doesn't actually live on the
b = 1 line. In a rigid fusion ring a self-dual simple τ has Hom(1, τ⊗τ) one-dimensional, so the
identity coefficient is pinned at 1. What varies is the τ-coefficient, which puts the particle
picture on c = 1. So the two pictures pin *different* invariants, sum and product, and share
exactly one equation. This page is that observation with its claims checked.

It pairs with `riemann-sphere.html`, where `1/z` is a half-turn of the sphere about the axis
through ±1. The orange swap here, `−1/z`, is the half-turn about the axis through ±i.

## What is checked (7 on load, re-run in `tests/test_crossing.cjs`)

1. Sum = 1 along b = 1 (Γ from −0.2 to 6) and product = −1 along c = 1 (n = 0 … 9).
2. `1 − z` swaps along b = 1, including Γ < −¼, where the roots are complex; `−1/z` along c = 1.
3. Each fails off its line.
4. Integer lattice search: both swaps work only at (1, 1).
5. The composition is `1 + 1/z`, fixed at φ and ψ, with the Fibonacci-ratio orbit.
6. Cassini's remainder S₍ₖ₋₁₎S₍ₖ₊₁₎ − Sₖ² is (−1)ᵏ·Γᵏ⁻¹ on b = 1 and (−1)ᵏ on c = 1, for every n tried.
   This check **failed on its first run**: I had written (−Γ)ᵏ, carried over from a note written
   earlier in the session. The kernel was right and the claim was wrong, so the claim was changed,
   not the tolerance. Both forms agree at Γ = 1, which is how the error survived until it was run.
7. Each line's own flow (replace the free parameter with the larger root): on b = 1 it ends at
   Γ = 2 from six starts; on c = 1 it is unbounded, ~√(2k). Neither ends at the crossing.

The Node test adds one check that can fail on purpose: a map that is not a swap is rejected at
every point tried.

## Not checked, and said so on the page

- That on c = 1 only n = 0 and n = 1 categorify (Ostrik 2003, arXiv:math/0203255). Cited, not shown.
- The rigidity argument that places the particle picture on c = 1 in the first place. Stated, not
  machine-checked.
- Any meaning. The page says that two parameter-free swaps agree at one equation. It does not say
  that equation is the centre of anything. As 09:06 asked of the sphere, nothing checks prose:
  this note's "where it came from" paragraph is the part to read with suspicion.

## A note on precision

`swaps()` compares with a 1e-9 tolerance. At (1, 1) the residuals are around 1e-16. Along c = 1
for large n the small root ≈ −1/n, so `−1/z` of it is ≈ n, and the comparison stays relative to
values of size n. With n up to 20 that's well inside the tolerance.
