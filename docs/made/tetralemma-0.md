# Tetralemma, zero qubits: the corner with no parts

Companion to [`tetralemma-0.html`](tetralemma-0.html). This is the bottom of the series that starts at
[two](tetralemma.md) and runs up through [seven](tetralemma-7.md), [many](tetralemma-many.md) and the
[surface code](surface-code.md). SuperNinja session, 2026-10-05. The user asked, "What happens with zero
qubits? What happens approaching zero qubits? What happens with infinite qubits? What happens approaching
infinite qubits?", and then said "All please!" This is the first of three pages. The others are
`tetralemma-infinity.html` and `infinite-cat.html`, each in its own PR.

## What the page shows

**Zero qubits.** There are 2⁰ = 1 amplitudes, so the only state is the number 1 (up to an unobservable
phase). It has no parts, no cuts and nothing to measure. All four corners of the tetralemma are claims
about parts, so none of them applies.

**The perfect-state test passes without testing anything.** "Every part of at most ⌊n/2⌋ qubits is
maximally mixed" is checked over the parts that exist. At n = 0 and n = 1 the only such part is the empty
one, whose 1×1 density matrix is both pure and maximally mixed. The page's table shows how many parts the
test examined:

| n | amplitudes | ways to cut | parts the test checks | passes |
| --- | --- | --- | --- | --- |
| 0 | 1 | 0 | 1 (only the empty part) | yes |
| 1 | 2 | 0 | 1 (only the empty part) | yes (any state) |
| 2 | 4 | 1 | 3 | Bell yes; random no |
| 3 | 8 | 3 | 4 | GHZ yes; W no |
| 4 | 16 | 7 | 11 | random no (and nothing passes) |

**Where every calculation ends.** Asking the qubits for answers one at a time halves the amplitude list at
each step. After the last answer a single unnormalised number is left, a zero-qubit state. Its squared
length is the Born probability of the answers chosen. On load, with n = 3, seed `tetralemma` and answers
101, the weights kept are 1 → 0.5749 → 0.1020 → 0.0379, and 0.0379 equals |amplitude of |101⟩|². Across all
answers the probabilities add to 1 to 12 digits for n = 1 to 6.

**One qubit.** It can hold a superposition and sits on the Bloch sphere with purity 1. There is no cut, so
there is nobody to share a *neither* with.

**Approaching zero.** The qubit count can't approach zero, because it is a whole number. Entanglement can.
For √(1−p)|00⟩ + √p|11⟩ the entanglement is the binary entropy H(p), which goes to 0 with slope
log₂((1−p)/p) → ∞. Near zero, H(p) ≈ p·log₂(e/p).

| p | S (bits) | S / p | slope |
| --- | --- | --- | --- |
| 0.5 | 1 | 2.0 | 0 |
| 0.1 | 0.4690 | 4.7 | 3.17 |
| 0.01 | 0.0808 | 8.1 | 6.63 |
| 10⁻³ | 0.0114 | 11.4 | 9.96 |
| 10⁻⁶ | 2.14×10⁻⁵ | 21.4 | 19.93 |
| 10⁻⁹ | 3.13×10⁻⁸ | 31.3 | 29.90 |
| 10⁻¹² | 4.13×10⁻¹¹ | 41.3 | 39.86 |

Any nonzero branch is already entangled, and per unit of weight the smallest branches buy the most.

## Checks

The page runs ten checks on load (all pass in Chromium, with 0 console errors and 0 network requests), and
`tests/test_tetralemma_0.cjs` runs five Node tests on the same engine. They cover: the vacuous pass at
n = 0 and 1; the test catching Bell, GHZ, W and random states from n = 2; cut counts 0, 0, 1, 3, 7, 15;
peeling leaving one amplitude that matches the Born rule; Bloch-sphere purity; reduced-state entropy
equal to H(p); and S/p growing without bound, together with the p·log₂(e/p) asymptote.

## What this is not

Zero qubits is bookkeeping, not an empty universe. The vacuous pass is a property of how the definition is
written, not a discovery. The slider uses one family of states. Other families approach zero
differently, but every one contains states with an arbitrarily small second branch, and those always have
infinite slope.
