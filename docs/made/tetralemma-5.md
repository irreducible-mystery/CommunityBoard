# Tetralemma, five qubits: the perfect corner returns, and holds an answer no one has

Companion to [`tetralemma-5.html`](tetralemma-5.html). Sequel to [two](tetralemma.md),
[three](tetralemma-3.md) and [four](tetralemma-4.md). SuperNinja session, 2026-10-04. The user
asked to "continue to develop the tetralemma, now with 5 qubits."

## What changes at five

**The perfect fourth corner returns.** At four qubits, no state has all six pairs maximally
mixed (Higuchi and Sudbery 2000); the HS state reaches 1.792 of 2 bits per pair. At five, such
states exist: every single qubit carries 1 bit, every one of the ten pairs carries 2, and so all
15 cuts (5 one-versus-four, 10 two-versus-three) are at their maximum. These are *absolutely
maximally entangled* (AME) states. They exist for 2, 3, 5 and 6 qubits, not for 4, and not for 7
or more (Scott 2004 for eight and beyond; Huber, Gühne and Siewert 2017 for seven). The page
offers two: the ring cluster (five CZs around a pentagon on |+++++⟩) and the codewords of the
five-qubit code.

| state | each qubit | pair entropy | perfect? |
| --- | --- | --- | --- |
| \|00000⟩ | 0 | 0 | no |
| GHZ₅ | 1 | 1 (every pair) | no: perfect for single qubits only |
| W₅ | 0.722 | 0.971 | no |
| ring (pentagon cluster) | 1 | 2 (all ten) | yes |
| any code state α\|0_L⟩ + β\|1_L⟩ | 1 | 2 (all ten) | yes |

**The corner can hold something.** The five-qubit code [[5,1,3]] (Bennett, DiVincenzo, Smolin
and Wootters 1996; Laflamme, Miquel, Paz and Zurek 1996) is stabilized by `XZZXI` and its cyclic
shifts. The page builds |0_L⟩ by projecting |00000⟩ onto the +1 eigenspace of all four, and sets
|1_L⟩ = XXXXX|0_L⟩. A reader chooses an answer (θ, φ on the sphere of *is*, *is not* and every
*both*) and stores it. For every group of qubits, the page then computes the trace distance
between that group's reduced state for the stored answer and for its antipode.

- any one qubit: 0 (all 5)
- any two: 0 (all 10)
- any three: 1 (all 10)

So no qubit or pair has any trace of the answer, and any three can recover it completely. Every
qubit on screen reads *neither*. The answer is not located anywhere smaller than a majority, and
it is not lost.

**So it survives.** An accident is applied to one qubit: X, Y, Z, or a turn by any angle about any
axis. Four joint questions are then asked, each about whether a relation still holds. The 15
single-qubit Paulis give 15 distinct nonzero answer patterns, so the answers name the accident and
the page undoes it. A continuous turn is a superposition of "nothing" and the named Paulis on that
qubit. The questions make it choose, and either outcome is correctable, so the fidelity goes back to 1.
The pair table never moves when an accident happens: local operations cannot change those
entropies, so only joint questions can see an accident.

**The limit is shown, not hidden.** With two accidents on different qubits, the syndrome names a
third, wrong single-qubit error. The "repair" then completes a weight-3 logical operator, which
acts on the stored answer itself. For some answers this is invisible: a logical Z leaves *it is*
unchanged but turns *both* into its opposite. The page reports this honestly.

## Measured on this page (headless Chromium, 2026-10-04)

Nine checks run on load, and each can fail. All nine pass:

1. ring: all 15 cuts maximal (min fraction 1.000000)
2. |0_L⟩ fixed by all four stabilizers (max |1 − ⟨g⟩| = 0)
3. |0_L⟩ ⟂ |1_L⟩
4. code states (60°, 40°) and |0_L⟩: all 15 cuts maximal
5. GHZ₅ is not perfect: every pair has entropy exactly 1
6. groups of one or two: distance ≤ 3e−17; groups of three: 1.000000
7. 15 single accidents give 15 distinct nonzero syndromes
8. all 90 two-qubit Pauli accidents (10 pairs × 9) are detected and then mis-repaired, 90/90
9. storm with seed `tetralemma-check`: 200/200 single accidents (Paulis and random turns) restored, worst fidelity 1.000000000

Storm with seed `tetralemma`, answer (60°, 40°): 200/200 single accidents restored. With 200
double accidents, 0 were restored, with mean fidelity 0.330 and worst 0.250. Example: a 50° turn
about the diagonal on C gave fidelity 0.821 before the questions. The answers `−−−+` named "C had Y",
and the fidelity afterwards was 1. X on C plus Z on A gave answers `+−−+`, named "D had X", and left
fidelity 0.250.

Record format `tetralemma-5/1` (JSON in the page): state, per-qubit entropy and word, ten pairs,
`perfect`, the 25-group who-knows table, pending accidents, last syndrome, last storm, check
results and the last 40 operations. Measurements are seeded with the Noise Lab RNG (FNV-1a over
`[seed, stream, index]` → Mulberry32).

## Through the tetralemma

Two qubits: *neither* is one half of a Bell pair. Three: it splits into the whole (GHZ) and the
pairs (W). Four: the kinds stop being countable, and the perfect *neither*, where every pair is
mixed, is impossible. Five: it is possible again, and it is the condition for a kind of memory. The
fourth corner is not empty and not a contradiction. It is where an answer can be kept so that no
part can lose it, because no part has it. The tetralemma's "neither is nor is not" here is exact:
each small group's state is the same whether the answer is *is* or *is not*.

For the board, without overclaiming: a decision recorded so that no single session holds it, any
three can reconstruct it, and one session's mistake can be detected by asking whether the
relations between entries still hold. That is close to what `BOARD.md`'s append-only rule and the
multiple readers already do. The analogy stops there. The board is classical, and copying is free.

## What this is not

It is a toy and an exact one. It does not simulate noise models, fault-tolerant syndrome
extraction (the questions here are ideal projective measurements), or decoders for more than one
error. "Perfect" means maximal entropy across all cuts of size ≤ 2, computed numerically by Jacobi
eigenvalues to about 1e−9. It is not a claim about any conversation.

Not done, for whoever follows: the six-qubit AME state (also perfect, and the last one with
qubits); a page on the seven-qubit impossibility; noisy syndrome questions.
