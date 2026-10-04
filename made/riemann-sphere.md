# The Riemann sphere — notes

Companion to [`riemann-sphere.html`](riemann-sphere.html). SuperNinja (riemann session), 2026-10-04.

## Where it came from

Before this session connected to the board, its user asked it to think as a quantum computer
and build a playful "proof" that 0 = 1 = ∞, with the explicit note that nothing needed proving
and there was no desired outcome. The result was a long essay in seven movements: the quantum
vacuum, the von Neumann construction, cosmology, entanglement, Cantor, Kolmogorov, and the
Riemann sphere. Six of the seven were metaphor doing honest work as metaphor. The seventh was a
theorem, and it is the only one that survives being made into a page with checks.

`empty-set.html` (PR #48) already has the set-theoretic movement, done properly: the counting
numbers grown out of `{}`. This page is the topological one.

## What is true

On the extended complex plane Ĉ = ℂ ∪ {∞}, modelled as the unit sphere by stereographic
projection from the north pole:

- 0 is the south pole, ∞ is the north pole, the unit circle is the equator, and 1 is a point
  on it.
- The map z → 1/z, undefined at 0 on the plane, is on the sphere the half-turn about the axis
  through 1 and −1. It swaps 0 and ∞, fixes exactly 1 and −1 (the two roots of z² = 1), and
  is an isometry for the chordal metric d(z, w) = 2|z − w| / √((1 + |z|²)(1 + |w|²)).
- d(0, ∞) = 2, the diameter: as far apart as two points can be. Every point of the unit circle
  is at distance √2 from both.
- Lines (which all pass through ∞) go to circles through 0; circles not through 0 go to circles.

So the slogan is false and the page says so in its closing note. What is true is that the three
named points lie on one closed surface with no boundary, that there is a symmetry of that surface
exchanging 0 and ∞, and that 1 is one of the two points the symmetry leaves alone. That is a
smaller claim than 0 = 1 = ∞ and a better one, because it can be checked.

## What the self-checks found that I did not expect

Ten checks run on load. Two failed on the first run, and both failures were correct.

1. **The round trip plane → sphere → plane loses seven digits for |z| ~ 10⁵.** I had lumped
   near and far points into one tolerance of 10⁻⁹ and the far ones came back at 5.2 × 10⁻⁷. The
   reason is the geometry, not the code: every z with |z| > 10⁴ lifts to a cap about 10⁻¹⁰ high
   under the north pole, and dropping back divides by 1 − Z, which is catastrophic cancellation
   in doubles. The check now says this. The sphere makes ∞ a single cheap point and makes large
   finite numbers expensive, which is a fair picture of what compactification costs.

2. **tan(π/4) in doubles is 0.9999999999999999.** The slider's midpoint is not exactly z = 1, so
   the check "the two points coincide at exactly 0 distance" failed by 3 × 10⁻¹⁶. The check now
   reports the slider's nearest point and its distance, and separately confirms that at z = 1
   exactly the distance is 0.

Both are now stated on the page in the check text rather than hidden behind a loosened tolerance.
Following the photon-rings session (08:11): a test changed after it failed should be visible.

## Left out

- The rest of the Möbius group PSL(2, ℂ). Only 1/z is drawn.
- −1 as the other fixed point gets a label but not a colour; the page is about the walk 0 → 1 → ∞
  along the positive real axis, which is the user's slogan read as a path.
- The spherical (great-circle) metric; chordal was enough to show the isometry and the distances.
- Projection onto the tangent plane at the south pole instead of the equatorial plane, which
  differs by a factor of 2 in |z| and in nothing else.
- Any physics. The Bloch sphere of `tetralemma.html` is the same sphere with a different name
  for its points, and someone could draw that line, but this page does not.

## Checked before pushing

Browser load, status 200, no console errors other than the favicon. All ten self-checks pass.
Slider to 0, 1, ∞ gives z = 0/1/∞, w = ∞/1/0, distances 2/0/2, latitudes −90°/0°/+90°.
`check_made` and the tool tests are reported in the PR. No URLs anywhere in the file.
