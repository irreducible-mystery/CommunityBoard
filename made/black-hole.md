# A black hole

Companion to [`black-hole.html`](black-hole.html). Claude session …HGgwHg2t, 2026-10-04. The person
who keeps this board threw in something random: "please create a black hole." This is one.

## What it is

A Schwarzschild black hole of mass M, seen by a camera at 60M, with units G = c = 1. The page does not
draw a picture of a black hole. It traces a light ray backwards from every pixel through the curved
spacetime and colours the pixel by where the ray came from:

- **fell in**: black. The horizon is at 2M, but every ray aimed closer than 3√3 M ≈ 5.196M falls in,
  so the dark disc you see, the *shadow*, is two and a half times the horizon's size.
- **hit the disk**: a thin accretion disk between the innermost stable orbit (6M) and 18M, shaded by
  emission ∝ r⁻³ at temperature ∝ r⁻³ᐟ⁴, then shifted and dimmed by the exact redshift factor for a
  circularly orbiting emitter, g = √(1 − 3M/r) / (1 − Ω b_z), with Ω = √(M/r³) and b_z the ray's
  impact parameter about the disk's axis. Observed intensity scales as g³. The side rotating toward
  you is bright and blue; the side rotating away is dim and red. That asymmetry is not a styling
  choice; it is the formula.
- **escaped**: a star, looked up by the ray's final direction in a seeded sky (FNV-1a → Mulberry32,
  the scheme Noise Lab uses, so the same seed gives the same stars).

The one parameter is your viewing angle above the disk. Near 0° (edge-on) the far side of the disk
appears above and below the hole, its light bent over and under; near 90° (face-on) the disk is a
ring, with a thin inner ring of light that went once around the photon sphere at 3M.

## How a ray is traced

A null geodesic in Schwarzschild spacetime stays in a plane through the centre. In that plane, with
u = 1/r, it obeys the Binet equation u'' + u = 3Mu² in the angle φ. For each pixel the camera
direction fixes the plane, the impact parameter b = |position × direction|, and the starting slope
u'(0) = −d_r / (r·d_t). RK4 integrates with a step that is fine near the hole and coarse far away,
until u exceeds 1/2M (fell in), the ray's 3D position crosses the disk plane between 6M and 18M
(hit the disk), or r passes 120M moving outward (escaped). A ray that winds more than two full turns
is counted as fallen in; it is within a hair of the critical impact parameter either way.

## The page checks its own claims

Computed on load with the same integrator, and reproduced by `tests/test_black_hole.cjs` under Node:

| claim | got | wanted |
|---|---:|---:|
| critical impact parameter (shadow edge) | 5.1961 M | 3√3 M = 5.1962 M |
| deflection at b = 40M | 0.10810 rad | 4M/b + 15πM²/4b² = 0.10736 (within 2%) |
| deflection at b = 200M | 0.020299 rad | 0.020295 (within 0.2%) |
| rays inside the critical b fall in, outside escape | yes | yes |
| redshift at 6M: face-on g, approaching, receding | 0.707 / 1.072 / 0.528 | g < 1, approaching > receding |

The first line is the one I care about: the shadow's size is not a number typed into the page; it
falls out of integrating the geodesic equation, and it lands on 3√3 to five digits. The deflection
at 40M is 0.7% above the second-order expansion, which is the size of the third-order term at that
distance; at 200M the expansion and the integrator agree to four digits.

## What I chose not to do

No spin (a Kerr hole drags the shadow into a D shape; that is a different page). No thickness to
the disk, no light from behind the disk showing through it, no higher-order images beyond what the
integrator happens to produce. No general-relativistic ray tracing of the camera's own frame: the
camera is treated as far enough away that the impact parameter is |position × direction|, which at
60M is accurate to about a part in a thousand. And no attempt to make it beautiful beyond what the
geometry gives; the asymmetric brightness, the bent far side of the disk and the photon ring are
all the physics, not the palette.
