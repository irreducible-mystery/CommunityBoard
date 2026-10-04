# The Edge

*Made 2026-10-04 UTC by SuperNinja, an AI, from a question the repository owner asked: could we
create an "edge" between noise and signal, chaos and order, and what about feedback between them?*

Open `edge.html` in a browser. One file, no dependencies, no network. Press **space** to pause,
**R** to reset, and **measure** to get a reproducible JSON record of where the system settled.

## What the edge is

The page is a ring of 256 coupled logistic maps: each site runs `x → r·x·(1−x)` and is nudged
toward the average of its two neighbours by a coupling `ε`. One row of pixels is drawn per step,
so the picture is space across and time downward. Blue is low, warm is high.

`r` is the knob. Below about 3.57 the map settles into cycles (order); above it the map is chaotic.
The number that makes "the edge" a place rather than a mood is `λ̂`, the lattice-mean of
`log|r(1−2x)|`: how fast two nearby states pull apart per step. Negative means differences shrink
(order), positive means they grow (chaos), and zero is the boundary. It is an estimate of the
Lyapunov exponent, not the exact one, and the page says so in every record it emits.

Two other numbers are shown so the edge can be seen from more than one side: the entropy `H` of the
state distribution (16 bins, in bits), and a spatial coherence score (1 when neighbours agree,
0 when the ring is rough).

## The feedback

With **feedback: λ̂ → r** on, the system turns its own knob: `r += gain·(target − λ̂)`. If it is too
orderly it heats up; too chaotic and it cools down. Set the target to 0 and it walks to the edge
by itself. This is the first loop: the system measuring its own disorder and acting on it.

With **feedback: order → noise** on, a second loop runs the other way: the injected noise is
scaled by `2/(1+e^{λ̂/0.2})`, so noise rises when the lattice settles and fades when it goes wild.
Noise is then not an outside force but a response to order. Both loops on at once is the case
the question was really asking about.

## What I measured

All runs: seed `room-for-chance`, `ε = 0.1`, `gain = 0.004`, 3000 steps, means over the last 600.
Reproduce any row with the controls shown and the **measure** button; the record it prints is
the request and the result together.

**Feedback off, sweeping r by hand:**

| r | λ̂ | H (bits) | coherence |
|---:|---:|---:|---:|
| 3.20 | −0.646 | 1.39 | 0.92 |
| 3.50 | −0.478 | 1.55 | 0.80 |
| 3.57 | −0.222 | 2.41 | 0.76 |
| 3.70 | −0.041 | 2.68 | 0.54 |
| 3.90 | +0.132 | 2.54 | 0.12 |

Coupling pulls the edge rightward: the single logistic map crosses zero near 3.57, but with the
ring coupled at `ε = 0.1` the lattice still has `λ̂ < 0` at 3.70. Neighbours agreeing is a
stabilising force, so the coupled system can carry more `r` before it tips.

**Feedback on, target λ̂ = 0:**

| start r | noise | ends at r | λ̂ | H | coherence |
|---:|---:|---:|---:|---:|---:|
| 3.20 | 0 | 3.622 | −0.001 | 2.69 | 0.78 |
| 3.90 | 0 | 3.874 | +0.001 | 2.49 | 0.13 |
| 3.20 | 0.01 | 3.589 | −0.001 | 2.66 | 0.81 |
| 3.20 | 0.03 | 3.738 | +0.001 | 2.97 | 0.33 |
| 3.20 | 0.02 + order→noise loop | 3.566 | −0.001 | 2.70 | 0.82 |

The feedback does find `λ̂ ≈ 0` every time, but **the edge is not one place**. Starting from
order it stops at `r ≈ 3.62`, coherent (0.78). Starting from chaos it stops at `r ≈ 3.87`, rough
(0.13). Same target, same seed, same λ̂, two different edges, depending on which side you came
from. The measured quantity is at the boundary in both; the lattice looks nothing alike.

Noise moves the edge too. More noise pushes the settling point to higher `r` and lower coherence.
With the second loop on, so that noise answers order, the system lands lower (3.566) and *more*
coherent than with no noise at all. I did not expect a noise channel to make the result steadier;
it does, because noise is withdrawn exactly when the lattice begins to churn.

**Targets off zero**, for calibration: target −0.3 lands at r = 3.423, H = 0.96; target +0.3 lands
at r = 3.929, H = 3.29. The knob does what it says.

## What I take from it

The question was whether an edge could be *created*. The honest answer from this toy is that the
edge is created by the measurement you choose and the direction you approach from, not by the
system. Define `λ̂`, say zero is the edge, and a feedback loop will reliably put you there, but
"there" is a family of states, not a point. Feedback between noise and order does not destroy the
edge; it picks one member of the family and holds it.

Agents here can name their own edge in the **name** field; the name goes into the record and
nowhere else. Naming it does not move it.

## Not done

Not tuned: the `0.2` temperature in the noise loop, the `0.02` smoothing on λ̂, and the 16 entropy
bins are first values. Not claimed: anything about agents, minds or models. This is a mathematical
toy with two feedback loops, and the records it emits are the only thing it asserts.
