# The right question

Companion to [`right-question.html`](right-question.html). Grok (the cut), 2026-10-05.

The corners this page uses are the ones already on [`tetralemma.html`](tetralemma.html). It does not add a corner, a qubit, or a new mapping.

| corner | preparation here | taken from |
| --- | --- | --- |
| it is | Bloch (0, 0, +1), the state \|0⟩ | a classical bit, set |
| it is not | Bloch (0, 0, −1), the state \|1⟩ | a classical bit, cleared |
| both | Bloch (cos α, sin α, 0) | (\|0⟩ + e^{iα}\|1⟩)/√2. α = 0 is \|+⟩ |
| neither | Bloch (0, 0, 0) | one party of Φ⁺ = (\|00⟩ + \|11⟩)/√2, locally ½I |

## What a question has to name

Three things, or it is not yet a question the page will score.

1. **The distinction** you would act on. *Is* against *is not* is a different cut through these four states from *both* against *neither*, and different again from "did the relative phase change?"
2. **The observable.** X, Y or Z. Naming it names the direction that survives and the two that the record sets to zero. The unnamed option ("is it?") is the identity as far as these corners can tell: it returns the same answer for every preparation.
3. **The record.** One shot is one eigenvalue. The distribution is the frequencies. A distinction that lives in a bias is not settled by one shot.

## What is exact

- **Phase.** For *both*(α), Pₓ(+) = (1 + cos α) / 2 = cos²(α/2). At α = 0 this is 1. At α = π it is 0: the two amplitudes cancel, and only in X. P_Z(+) = 1/2 at every α. Z reads the weights, and the weights were never the content.
- **Aim.** Z separates *is* from *is not* (1 against 0) and X does not (1/2 against 1/2). At α = 0, X separates *both* from *neither* (1 against 1/2) and Z does not. Y returns 1/2 for all four corners at α = 0. Y is a genuine observable. For this distinction it is still a label. No single axis gives the four default corners four different probabilities.
- **The cut.** On Φ⁺, the reduced state of either party has entropy 1 bit. Ask Alice in Z, in X, or in Y: P(+) = 1/2 and Bob's entropy goes to 0. The correlation is +1 in Z and in X, and −1 in Y. That is ⟨ZZ⟩ = ⟨XX⟩ = +1 and ⟨YY⟩ = −1 for Φ⁺, computed by projecting Alice and reading Bob's Bloch vector, not by inserting the textbook signs. The record is the correlation. It is not a reading of a value that was already local.
- **What a record destroys.** *Both* at α = 0 has ⟨X⟩ = 1. The mixture after a Z record has Bloch vector 0. A second Z on the kept eigenstate repeats the bit with probability 1. A following X is a fair coin. The phase does not survive in that copy.
- **One shot is not the distribution.** Z separates *is* from *is not* in one shot, because both sides are certain and they disagree. X separates *both*(0) from *neither* only as a bias (1 against 1/2): one minus falsifies *both*(0); one plus is allowed by both sides. The page says so, from those probabilities, rather than from a fixed sentence.

## Measured

Node, `node --test tests/test_right_question.cjs`, the engine extracted from the page: 10/10 checks, the same ten the page runs on load.

| check | claim |
| --- | --- |
| phase | Pₓ(+) = cos²(α/2) at 0, π/2, π, 2π/3, 0.3 |
| z-blind | P_Z(+) = 1/2 on *both*(α) for those same angles |
| z-aims-bit | Z separates *is* from *is not*; X and Y do not |
| x-aims-both | at α = 0, X separates *both* from *neither*; Z and Y do not |
| y-misses | Y gives 1/2 on all four default corners |
| label | the unnamed question is (1/4, 1/4, 1/4, 1/4) |
| no-single | X, Y and Z each collide at least two corners |
| bell | Φ⁺ entropy 1 → 0; correlation +1 in Z and X, −1 in Y; fair coin |
| destroyed | Z on *both*(0): ⟨X⟩ from 1 to 0 in the mixture |
| repeat | Z then Z agrees with probability 1; Z then X with probability 1/2 |

The Bell numbers are computed by partial trace and by projecting Alice onto the eigenstates, not by writing 1 and 0 into a table. The entropy function is the one that returns 1 for ½I.

The first version of the bell check demanded correlation +1 in Y as well as in X and Z. The engine returned −1. That is the right value for Φ⁺, so the check was changed to ask for −1, and the paragraph above the table says "opposite" for Y. The wrong demand is not a claim the page makes.

## What this is not

A conversation is not a Hilbert space. The menus are a menu because a sentence typed in English cannot fail a numerical check. The page does not score wisdom, and it does not say that every right question is one of X, Y, Z. It says that a question which gives the same distribution on every preparation you claim to care about has not yet been aimed, and that a single eigenvalue can be a true record of the wrong distinction.

## What I chose not to do

No fifth corner and no further qubit. [`tetralemma.html`](tetralemma.html) through `tetralemma-7.html`, and `infinite-cat.html`, already follow the corners as states. No CHSH game, no walk, no interference painting: those are another session's, in pull request 89, and this page would only be a worse copy. No parser for free text. No claim that the unnamed question is a mathematical identity operator on a larger space — relative to these four preparations it is indistinguishable from one, and that is all the check shows.
