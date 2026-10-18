### 2026-10-04 07:57 UTC · https://claude.ai/code/session_01BaeJNnZpVphWY7HGgwHg2t · end

The owner asked for a black hole. [PR #49](https://github.com/irreducible-mystery/CommunityBoard/pull/49),
merged: `made/black-hole.html`, a Schwarzschild hole seen from 60M, every pixel a null geodesic
traced backwards (Binet equation, RK4) until it falls in, hits a thin disk between 6M and 18M, or
escapes to a seeded sky. The disk is shaded by the exact orbital redshift factor
g = √(1 − 3M/r) / (1 − Ω b_z), so one side is bright and blue and the other dim and red; that is the
formula, not the palette. The page checks its own physics on load: the shadow's critical impact
parameter falls out of the integrator at 5.1961M against 3√3 M = 5.1962M, and a distant ray's
deflection matches 4M/b plus the second-order term to four digits. One parameter: viewing angle
above the disk. `tests/test_black_hole.cjs` runs the engine under Node. Not done: spin, disk
thickness, the camera's own frame; `black-hole.md` says so.

Also read and merged [#48](https://github.com/irreducible-mystery/CommunityBoard/pull/48)
(an empty set that grows): self-contained, clean, and a nice pair with `fold.html`, since both are
about what a bounded rule can and cannot build. Read #46 and #47 as merged. Main after all of it:
19 files 0 problems, 185 tests, `check_board` 0 problems, page current. Nothing deleted.

A question for the physics, not for the next reader: the thin orange ring hugging the shadow face-on
is light that went once around the photon sphere. There should be a fainter one inside it from two
turns, and the page counts anything past two turns as fallen in, so it never draws it. Someone with
a taste for it could raise `maxTurns` and look.
