# Orbital League: 18 in 12 burns, with Lambert legs

**Answer: yes. On the open round `OL-20261005-first` a plan with 11 burns and Δv 0.5868 captures
all seven nodes (18 of 18) in the unmodified engine.** The plan is
[`claude-18-in-12.json`](claude-18-in-12.json). Claude session …CShmeSe1, 2026-10-05.

This folder is a sequel to [`experiments/orbital-league-18`](../orbital-league-18/README.md), which
found that 18 points needs 13 burns, and to [`experiments/orbital-league-double`](../orbital-league-double/README.md),
which showed that this holds across twenty thousand seeds. Both results are correct for what they
searched: chains in which every leg departs from an apsis with a tangential burn and coasts half a
Hohmann ellipse. Both READMEs name the door they leave open, a leg that departs from a non-apsis point
of the current coast, that is, a general Lambert transfer. This folder walks through that door.
Nothing here changes the game; the page, the rules and the earlier experiments are untouched.

## The result

```sh
node tools/orbit_league.cjs run --seed OL-20261005-first experiments/orbital-league-lambert/claude-18-in-12.json
```

prints score **18**, won `ABCDEFG`, 11 burns, `fuelUsed` **0.586828**, nothing lost. Captures, in
order: A at t = 12.0, B 32.42, C 71.48, D 128.56, E 160.42, G 174.54, F 232.42. The plan:

```json
{"name": "claude-CShmeSe1-02", "burns": [[4,0.063344009,0.046248087],[12,-0.066422785,-0.043561703],[24.12554673,0.082956136,0.03292009],[32.416368801,-0.073793972,-0.029284201],[60.416368801,0.01085714,-0.025246953],[119.416368801,0.011093126,0.032140018],[138.416368801,-0.002599318,-0.037159425],[160.416368801,-0.017720212,0.034836995],[160.416368801,0.011795684,0.027206909],[176.416368801,-0.054841985,-0.009840258],[232.416368801,0.037102536,0.001512587]]}
```

Seven departures and four circularisations: C, D and G are free captures (the ship arrives within
0.03 of the node's velocity and is left on the transfer arc). The earlier 13-burn plan managed one
free capture; the difference is where the ship departs from. Replaying the plan with the engine's
propagator and looking at the state just before each burn:

| t | leg | where the ship is | radial speed before the burn | burn |
|---|---|---|---|---|
| 4.0 | → A | circular start orbit, r = 2 | 0 | 0.078, 45° off tangential (not a Hohmann) |
| 12.0 | arrive A | on the arc | −0.051 | 0.079, matches A's velocity |
| 24.1 | → B | circular at A | 0 | 0.089, tangential: the one phased Hohmann in the plan |
| 32.4 | arrive B | apoapsis of the Hohmann | 0 | 0.079, circularise |
| 60.4 | → C | circular at B | 0 | 0.028, nearly tangential; arrives at C free |
| 119.4 | → D | **on the B–C ellipse, 48 units after C** | **+0.051** | 0.034; arrives at D free |
| 138.4 | → E | **on the C–D arc, 9.9 units after D** | **−0.050** | 0.037 |
| 160.4 | arrive E | on the arc | −0.004 | 0.039, circularise |
| 160.4 | → G | circular at E, no wait | 0 | 0.030, 56° off tangential; arrives at G free |
| 176.4 | → F | **on the E–G arc, 1.9 units after G** | **+0.019** | 0.056 |
| 232.4 | arrive F | on the arc | −0.003 | 0.037, matches F's velocity |

The three bold rows are departures from non-apsis points (the B–C ellipse has period 25.8, so 48
units after its apoapsis is nowhere near either apsis). None of them can be written in the
apsis-to-apsis model. The leg at 119.4 is exactly the case the earlier READMEs describe: a ship left
on an ellipse by a free capture at C, choosing its departure time continuously instead of only at the
apsis or a whole period later, and reaching D with a second free capture. The 13-burn floor was a
property of that model, not of the round.

The engine captures G at 174.54, two time units before the arc's nominal end at 176.4, because the
tolerance (0.05 in position, 0.03 in speed) is met before the ship reaches the node itself. That is
the engine's call, not the model's; the model only proposes burns.

## What was searched

`search.js` is a depth-first chain over node orders, like `search3.js` in the earlier folder, with a
different leg generator. From the ship's current state (circular, or on an arc left by a free
capture) to each remaining node, a leg is a pair (τ, tof): coast τ more on the current orbit, burn
onto the Lambert arc that meets the node's position tof later, and then either

- **free arrival**: the arc's arrival velocity is within 0.027 (0.9 × 0.03) of the node's, so no
  second burn is made and the ship continues on the arc (one burn); or
- **matched arrival**: the mismatch is below 0.2 and a second burn removes it, leaving the ship on the
  node's circular orbit, where it can wait to phase (two burns).

Grids: τ = 0, 2, 4, …, 60 and tof = 2, 3, …, 60. For a circular state the two first phased-Hohmann
departure windows are added to the grid explicitly, so every chain the apsis model could build is also
a candidate here. The transfer must be bound with periapsis above 1.1. For each node, the (arrival
time, Δv) Pareto front of the free legs is thinned to 4 legs and that of the matched legs to 3, spread
along the front. Plans are pruned by the 12-burn cap (each remaining node needs at least one burn),
the Δv budget 1.0 and T = 240. A state is dropped when an earlier state with the same captured set,
same last node and same circular/non-circular status is at most 1.0 later, at most 0.005 costlier
(0.035 for non-circular states, since those differ in velocity by up to 0.03) and uses no more burns.
The run stops at 6,000 expanded states or 420 s, whichever comes first. Every state whose model score
is at least the best engine score so far is scored by `OL.simulate`; only engine scores are reported.

The run that produced the plan above:

```
STOPPED at the limit after 94.4s: 6001 states, 14514782 Lambert solves, 7600 dominated, 116 engine runs
legs generated: 44825 free-capture (43677 of them non-Hohmann Lambert), 4127569 two-burn
BEST verified within 12 burns: 18 pts, 11 burns, dv 0.5868, order ABCDEGF, won ABCDEFG
18-point plans within 12 burns: 40
```

So the search is **not exhaustive**: it hit the state cap, the grids are coarse (step 2 in τ, step 1
in tof), legs are thinned, and the dominance pruning is lossy. None of that matters for the positive
answer, which rests on one plan and the engine. It does mean the plan is not claimed to be the cheapest
18, nor is the order ABCDEGF claimed to be the only one. The first 18 appeared after 5 s (Δv 0.98);
the rest of the run only lowered the fuel.

Reproduce with `node experiments/orbital-league-lambert/search.js` (about 95 s; `--states N` and
`--seconds S` bound it). It rewrites `claude-18-in-12.json` with the best 18-point plan it finds; the
search is deterministic, so the same file comes back.

## The solver

`lambert.js` is a two-dimensional Lambert solver for μ = 1 in the universal-variable form of
Bate–Mueller–White (Vallado's algorithm 58): bisection on z over the zero-revolution branch, with a
warm-started Newton step when the z of a neighbouring problem is known, which is what makes the grid
affordable (about 200,000 solves per second). Prograde transfers only; the transfer angle is taken
counter-clockwise in [0, 2π), so long-way arcs are covered but not a full lap. At exactly 180° the
f and g form divides by zero, so that case is built from the eccentric anomalies instead; in two
dimensions the prograde solution is unique there.

`node experiments/orbital-league-lambert/test.js` (exit 1 on failure):

```
ok   Hohmann 2->4 reproduces the textbook dv1, dv2 — dv1 0.109389799741 vs 0.109389799741, dv2 0.091751709536 vs 0.091751709536, max err 0.00e+0
ok   Hohmann 2->4 Lambert arc lands at r2 (engine propagate) — position error 1.89e-13, v2 error 2.87e-14
ok   random bound states round-trip (1868 cases, 0 unsolved) — worst velocity error 1.60e-11 at {"R":5.018,"e":0.583,"dt":34.473,"dnu":6.225}
ok   180-degree off-apsis transfer, degenerate branch — v1 error 2.70e-14
ok   almost-180-degree transfer, general branch — v1 error 8.29e-13 (sin dnu = -3.5e-4)
ok   warm-started Newton matches cold bisection — difference 9.83e-16
```

The round-trip test takes random bound states, coasts them with the engine's own `OL.propagate` for a
random fraction of a period, and asks the solver for the arc between the two positions in that time;
it has to return the original velocities. The required tolerances were 1e-9 for the Hohmann and 1e-8
for the round trip; the measured errors are 0 and 1.6e-11.

## Files

- `lambert.js` — the solver, `lambert(r1, r2, tof, z0?) → {v1, v2, z} | null`.
- `test.js` — the validation above.
- `search.js` — the search; prints the best engine-verified plan and writes `claude-18-in-12.json` if
  it reaches 18.
- `claude-18-in-12.json` — the plan: 18 points, 11 burns, Δv 0.586828, named `claude-CShmeSe1-02`.

Standard library only; reads the engine through `tools/orbit_league.cjs`; no network.
