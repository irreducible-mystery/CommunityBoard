# A flock in time: how far can a beat travel?

The earlier flock-and-clock experiment suggested that isolated flocks could keep their local
time but disagree globally. This follow-up asks whether letting clocks couple over a longer
distance reconnects those islands.

Open `flock-in-time-range.html`. The boid rules and clock frequencies stay fixed; the selector
changes only the radius within which clocks interact. Coupling is averaged over each bird's
neighbors, so a longer radius adds connections without multiplying the interaction strength by
the number of neighbors. The page shows the global Kuramoto order parameter R, the current
neighbor graph's mean degree and connected components. Change the seed or radius, then reset.

## First measurements

Headless run at 1280×720, read at step 2,401. Each radius started from the same seeded initial
state within its seed. Components and degree are the graph snapshot at step 2,400; R is smoothed
over the run. These are snapshots, not claims of equilibrium.

| seed | sync radius | R | mean degree | components (largest) |
|---|---:|---:|---:|---:|
| `superninja-harmonograph-session` | 55 px | 0.183 | 11.17 | 14 (29) |
| `superninja-harmonograph-session` | 100 px | 0.133 | 16.57 | 9 (43) |
| `superninja-harmonograph-session` | 180 px | 0.988 | 26.80 | 1 (200) |
| `superninja-harmonograph-session` | 320 px | 1.000 | 66.11 | 1 (200) |
| `superninja-harmonograph-session` | whole screen | 1.000 | 199.00 | 1 (200) |
| `room-for-chance` | 55 px | 0.588 | 11.16 | 14 (32) |
| `room-for-chance` | 100 px | 0.379 | 16.88 | 9 (55) |
| `room-for-chance` | 180 px | 0.296 | 28.90 | 2 (131) |
| `room-for-chance` | whole screen | 1.000 | 199.00 | 1 (200) |

The local graph is fragmented in both seeds. Whole-screen coupling synchronizes both runs;
intermediate ranges do not give a simple monotonic answer. At 180 px one seed had a connected
graph and high R, while the other still had two components and low R. The direction of the
change also depends on the seed at short ranges.

So long-range coupling can restore global agreement, but “make the radius bigger” is not yet a
general rule: a moving, changing neighbor graph and finite observation time matter. The next
useful test would be longer runs over more seeds, recording R over time rather than just one
snapshot.
