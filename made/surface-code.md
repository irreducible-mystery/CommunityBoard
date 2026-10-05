# Surface code: where the tetralemma goes when it has to do work

Companion to [`surface-code.html`](surface-code.html). It is the third of three pages written after the user
asked "what happens as we continue to add qubits?" and then said "All three please". The other two are
`tetralemma-7.html` (PR #74) and `tetralemma-many.html` (PR #75), both open when this was written.
SuperNinja session, 2026-10-05.

## The idea

The five-qubit page stored one answer that no qubit and no pair could see, and four joint questions could
undo any single accident. The random-state page shows that hiding is almost free in a large system. Repair
is not free. A surface code is a large system built so that repair works. Qubits sit on a d×d grid.
Each check asks a small neighbourhood whether its X's (or its Z's) are even. The stored answer is not in any
neighbourhood. It is a property of chains that run from one edge to the opposite edge: Z along a row, X down a
column. This is the *neither* from the earlier pages spread across a grid. A row is a minimal group that holds
the answer, and any smaller group holds nothing about it.

## What the page does

- **The code.** This is a rotated planar code of distance d (3 to 15). Clicking a qubit adds an X, Z or Y
  accident. The lit checks show, a union-find decoder (Delfosse and Nickerson 2017) proposes a repair, and the
  page says whether applying it would restore the code or complete a chain across it.
- **Accidents one at a time.** Random accidents are added until the decoder is first fooled. Each
  distance gets 50 seeded runs.
- **The threshold.** A sweep of p from 3% to 15% for d = 3, 5, 7, 9 and 11, each qubit independently
  hit by X and by Z with probability p (code capacity, perfect checks).
- **Ten checks on load**, a JSON record, and a seeded RNG. There are no dependencies and no network access.

## Numbers from a run (seed `tetralemma`, default settings)

Accidents until first fooled, 50 runs each:

| d | qubits | always repaired up to | fewest | median | mean | most |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 9 | 1 | 2 | 2 | 3.1 | 9 |
| 5 | 25 | 2 | 3 | 6 | 6.3 | 15 |
| 7 | 49 | 3 | 5 | 11 | 11.2 | 23 |
| 9 | 81 | 4 | 6 | 15.5 | 16.3 | 33 |
| 11 | 121 | 5 | 10 | 22 | 22.5 | 45 |

No run was fooled at or below the guarantee of (d−1)/2. Typical runs survive far beyond it, because
accidents scattered on a big grid are mostly far apart.

Logical failure rate, 1000 trials per point:

| p | d=3 | d=5 | d=7 | d=9 | d=11 |
| --- | --- | --- | --- | --- | --- |
| 3% | 0.036 | 0.013 | 0.004 | 0.001 | 0.001 |
| 5% | 0.092 | 0.058 | 0.052 | 0.036 | 0.020 |
| 7% | 0.145 | 0.124 | 0.134 | 0.116 | 0.099 |
| 9% | 0.226 | 0.205 | 0.235 | 0.223 | 0.222 |
| 10% | 0.270 | 0.252 | 0.296 | 0.324 | 0.301 |
| 11% | 0.311 | 0.311 | 0.351 | 0.339 | 0.369 |
| 13% | 0.351 | 0.413 | 0.462 | 0.491 | 0.500 |
| 15% | 0.420 | 0.473 | 0.530 | 0.582 | 0.612 |

On this run the d = 3 and d = 11 curves cross near p ≈ 9.1%. The published union-find threshold for this noise
model is about 9.9%. With 1000 trials per point the crossing is only approximate. The intermediate
distances are noisy near the threshold, and d = 7 at 7–9% sits slightly above d = 5. That is sampling noise,
plus the fact that the small-d curves cross at slightly different points. The page says it gives an estimate,
not a three-digit measurement.

## What was verified

The checks run on load and again in `tests/test_surface_code.cjs`:

- For d = 3 to 15, every X check overlaps every Z check evenly, and each type has rank (d²−1)/2, leaving
  one stored qubit.
- A row of Z and a column of X commute with every check.
- Every single accident is repaired at d = 5, 7 and 9, and every pair at d = 5 (600 cases).
  During development every triple at d = 7 (36,848 cases) was also checked.
- A line of (d−1)/2 X accidents down column 0 is repaired, and (d+1)/2 fools the decoder (d = 3 to 11).
- A full row of Z lights no check and is the logical Z. X on any one X check's qubits is a stabilizer.
- Repairs always clear every lit check.
- d = 7 fails less than d = 3 at p = 3% and more at p = 15%.

## What this is not

This is a code-capacity toy. Accidents strike the data qubits, the checks are read perfectly, and X and
Z are decoded independently. Real devices also make errors when measuring, so checks must be repeated
over time and decoded in three dimensions, which pushes the threshold down to about 1%. The decoder here
is union-find. It is not the best decoder: minimum-weight matching reaches about 10.3% and the optimal
decoder about 10.9% on this noise model.
