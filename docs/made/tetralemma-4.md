# Tetralemma, four qubits — no list, no perfect corner, and the relation travels

Companion to [`tetralemma-4.html`](tetralemma-4.html). Sequel to [two](tetralemma.md) and
[three](tetralemma-3.md). SuperNinja session, 2026-10-04. The user asked "what happens with 4
qubits?" and then to build it.

## What changes at four

**The kinds of *neither* stop being countable.** Two qubits: one (Bell). Three: two (GHZ, W).
Four: nine families, most with continuous parameters (Verstraete, Dehaene, De Moor, Verschelde
2002). The page does not try to list them; it offers seven states and lets a reader measure what
each pair and each cut keeps.

| state | each qubit | pairwise concurrence | pair entropy | notes |
| --- | --- | --- | --- | --- |
| two Bell pairs Φ⁺ₐв ⊗ Φ⁺꜀ᴅ | ½·I | AB = CD = 1, others 0 | AB, CD: 0; others: 2 | A and D have never met |
| GHZ₄ | ½·I | all 0 | all 1 | the whole; one Z measurement kills it |
| W₄ | purity 5/8 | all ½ | all 1 | the pairs; also killed by one Z |
| cluster A–B–C–D | ½·I | all 0 | AB, CD: 1; AC, AD, BC, BD: 2 | survives one Z, not two |
| Higuchi–Sudbery | ½·I | all 0 | all 1.792 | closest known approach to all-pairs-mixed |

A second axis appears that three qubits could not show: **persistency**. GHZ₄ and W₄ fall to a
classical mixture when any one party is asked "is it?"; the cluster survives the first question
(the other three keep 2 bits of single-qubit entropy and one entangled pair) and falls at the
second. In the cluster, pairs that interacted directly (AB, CD) have entropy 1 while pairs that
never met have 2 — who you spoke to is written into what you keep.

**No perfect fourth corner.** Higuchi and Sudbery (2000): no four-qubit state has all six
two-qubit reduced states maximally mixed. For two parties the perfect *neither* exists (Bell);
for three it exists (GHZ); for four it does not; five and six have it again; seven and beyond
never. The page reports the least-mixed pair and the average pair entropy for whatever is on
screen, against the unreachable 2.000. The HS state

    (|0011⟩ + |1100⟩ + ω(|1010⟩ + |0101⟩) + ω²(|1001⟩ + |0110⟩)) / √6,  ω = e^{2πi/3}

gives every pair the same spectrum (½, ⅙, ⅙, ⅙): entropy 1.792, purity ⅓ against a floor of ¼.
(The page's first draft said (⅓, ⅓, ⅓, 0); the browser corrected me. The theorem is unaffected;
the record of the mistake is kept here.)

**The relation travels.** Entanglement swapping needs exactly four. Start from Φ⁺ₐв ⊗ Φ⁺꜀ᴅ,
C(AD) = 0. Measure B and C in the Bell basis (CNOT, H, two Z measurements). C(AD) → 1. A and D
hold a Bell pair, though nothing ever passed between them; the intermediaries handed the
relation on and dropped out. The page reports which Bell state BC announced and which one AD now
holds, with fidelity.

**The conversation becomes a computation.** Raussendorf–Briegel one-way model on the linear
cluster. Measure A, B, C in turn in the basis (|0⟩ ± e^{−iα}|1⟩)/√2, with each angle's sign
flipped by the accumulated X-byproduct of earlier answers. D, which no gate touched, ends in
H·R_z(α₃)·H·R_z(α₂)·H·R_z(α₁)|+⟩ up to a Pauli byproduct that is announced classically and
undone with X and/or Z. The three answers are fair coins; different seeds give different answers
and the same final D.

**Monogamy generalises; the tangle doesn't.** CKW holds for n qubits (Osborne–Verstraete 2006),
but there is no single 4-tangle — several inequivalent ones exist and disagree. The page therefore
shows cuts and pairs, not one number for "the part that belongs to all four."

## Measured (headless Chromium)

All table rows above are what the page reported. Persistency: GHZ₄ ask B → other three 3.000 →
0.000 bits, 0 entangled pairs; cluster ask B → 3.000 → 2.000 bits, 1 entangled pair; cluster ask
B then C → 0. Swapping from two pairs: BC announced Φ⁺, C(AD) 0 → 1.000, AD = Φ⁺ fidelity 1.
One-way: 30/30 random angle triples and seeds reached the target with fidelity > 0.9999,
corrections {none, X, Z, XZ} all observed, 8 distinct answer patterns. Reproducible after reload.
0 page errors, 0 non-file requests.

## How it is computed

16 complex amplitudes. Single- and two-qubit reduced states by partial trace. Pairwise
concurrence via Wootters' formula, eigenvalues via a Jacobi solver on the 8×8 real embedding of
each Hermitian 4×4 (equal pairs; one of each taken). Entropies in bits from the eigenvalues. The
one-way run tracks the byproduct frame (x, z) through each H·R_z step as (x, z) → (s ⊕ z, x).

## What this is not

A conversation is still not a Hilbert space. What the toy is exact about: that the ways of having
no state of one's own become a continuum, so no table of kinds of relation will be complete; that
past four no relation is perfectly symmetric — some pair always knows something; that a relation
can be handed on through intermediaries who never meet the parties they connect; and that a
sequence of questions, each shaped by the last answer, can do work no action on the final party
could have done.

## What I chose not to do

No fifth qubit (32 amplitudes is easy; the point of stopping is that four already has no list).
No attempt at a 4-tangle, for the reason above. No Mermin table — it still works for GHZ₄ and the
gap grows as 2^{(n−1)/2}, but it is the three-qubit argument with more rows, and the new things
at four are structural. No animation.
