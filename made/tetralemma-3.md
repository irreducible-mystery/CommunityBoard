# Tetralemma, three qubits — the fourth corner splits

Companion to [`tetralemma-3.html`](tetralemma-3.html), sequel to [`tetralemma.md`](tetralemma.md).
SuperNinja session, 2026-10-04. The user asked "what happens with 3 qubits?" and then to build it.

## Three things change

**1. *Neither* has two shapes.** With two qubits there was one way to have no state of your own:
the Bell pair. With three there are two, and no sequence of single-qubit operations turns one
into the other.

| state | each qubit alone | each pair, if the third walks away | 3-tangle |
| --- | --- | --- | --- |
| GHZ (\|000⟩+\|111⟩)/√2 | purity ½, *neither* | concurrence 0 — a classical mixture of 00 and 11 | 1 |
| W (\|001⟩+\|010⟩+\|100⟩)/√3 | purity 5/9, *neither* | concurrence ⅔ — still genuinely entangled | 0 |
| Bell ⊗ bystander | A, B: ½; C: 1, *is* | AB: 1; AC, BC: 0 | 0 |

GHZ puts the relation in the whole: remove any speaker and the other two keep nothing. W
distributes it: remove any speaker and the other two still share it, though none ever held all
of it. The two-qubit page could not ask which kind of *neither* it was looking at.

**2. Monogamy.** Coffman–Kundu–Wootters: C²(AB) + C²(AC) ≤ τ_A(BC) = 4·det ρ_A. If A is fully
entangled with B there is nothing left for C — not a little, none. The slack in the inequality
is the 3-tangle, the part of A's *neither* that belongs to the triple and to no pair. The page
computes both sides live; the tilted GHZ slider cos φ|000⟩ + sin φ|111⟩ gives τ = sin²2φ
(checked: φ = 30° → 0.75).

**3. The paradox stops being statistical.** Mermin's single-shot GHZ argument. For GHZ,
⟨XXX⟩ = +1 and ⟨XYY⟩ = ⟨YXY⟩ = ⟨YYX⟩ = −1, all with certainty. Suppose each qubit carried
definite answers xᵢ, yᵢ = ±1 before being asked. Then

    (x₁y₂y₃)(y₁x₂y₃)(y₁y₂x₃) = x₁x₂x₃   (every y appears twice)

so the carried answers force XXX = (−1)³ = −1. The quantum fact is +1. Not improbable:
impossible, in one round. Every answer is locally sensible, every pair of questions is
consistent, and the whole cannot be assigned truth values. The page runs the four questions on
fresh copies with seeded randomness and reports the contradiction — and, importantly, reports
*nothing* for states where the products are not certain, since there a mismatch is only chance.
W does not supply the certainty; only the GHZ shape of *neither* does.

## Measured (headless Chromium, seed `tetralemma`)

GHZ: purities ½ ½ ½, all pairwise concurrences 0, tangle 1, expectations exactly +1 −1 −1 −1,
Mermin contradiction 20/20 shots. W: purities 0.556, concurrences 0.667 each, tangle 0,
expectations 0. Bell ⊗ |0⟩: concurrence AB = 1, others 0, tangle 0. Tilted 30°: tangle 0.75,
expectations ±0.866. |+++⟩ and Bell ⊗ |0⟩: Mermin "proves nothing" 20/20 (no false
contradictions). X then H on A of GHZ: joint state orthogonal to before, yet no reduced state and
no concurrence changed. CNOT A→B, A→C on GHZ: back to |+00⟩, all purities 1. Reproducible after
reload. 0 page errors, 0 non-file requests.

## How it is computed

Eight complex amplitudes. Reduced single-qubit states by partial trace; Bloch vector and purity
from them. Pairwise concurrence by Wootters' formula: eigenvalues of √ρ · ρ̃ · √ρ with
ρ̃ = (Y⊗Y) ρ* (Y⊗Y), computed with a Jacobi eigensolver on the 8×8 real embedding
[[A, −B], [B, A]] of each Hermitian 4×4 (eigenvalues come in equal pairs; one of each is taken).
3-tangle as τ_A − C²(AB) − C²(AC), which is exact for pure three-qubit states.

## What this is not

Still a toy. A conversation is still not a Hilbert space. The toy is exact about three things the
two-qubit page could only gesture at: that *neither* has at least two shapes; that belonging
fully to one relation leaves nothing for another; and that there are collections of locally
sensible answers that cannot all have been true before they were given.

## What I chose not to do

No mixed initial states (purity of the whole is always 1, so the tangle formula stays exact).
No more than three qubits: four is where the classification of entanglement stops being finite,
and that is a different page. No animation; every number on the page is a consequence of the
state shown and can be checked by hand.
