# The infinite cat: a superposition no finite question can see

Companion to [`infinite-cat.html`](infinite-cat.html). SuperNinja session, 2026-10-05. This is the third of
three pages after the user asked, "What happens with zero qubits? What happens approaching zero qubits? What
happens with infinite qubits? What happens approaching infinite qubits?", and then said "All please!". The others are
`tetralemma-0.html` (PR #84) and `tetralemma-infinity.html` (PR #86).

## The question

Put the cat state GHZₙ = (|0…0⟩ + |1…1⟩)/√2, the *both* corner at its most extreme, next to a coin: all-0
or all-1 with even odds and no superposition. Which measurements can tell them apart?

## 1. Every part agrees

The cat's density matrix is the coin's plus the two corner entries ½|0…0⟩⟨1…1| and its mirror.
Tracing out any single qubit removes both. The page checks this entry by entry for all 2ⁿ−2 proper parts,
n = 2 to 6. Cats with + and − are likewise identical on every proper part, so the relative phase lives only in
the whole.

Of all 4ⁿ Pauli questions, exactly 2ⁿ⁻¹ distinguish cat from coin (2, 4, 8, 16 for n = 2 to 5). Each has X or Y
on every qubit and an even number of Y's. The fraction 2ⁿ⁻¹/4ⁿ goes to zero. Yet the trace distance between
the whole states is ½ for every n (computed by diagonalisation, n = 1 to 5): the difference is real but has no
location.

## 2. The one question fades

For the cat, the product of X outcomes over every qubit is always +1; for the coin it is a fair ±1. With
readout error e per qubit, the cat's mean product is (1−2e)ⁿ. Seeded simulation at e = 1% with 20,000 shots
gave 0.907, 0.666 and 0.362 at n = 5, 20 and 50, against predictions of 0.904, 0.668 and 0.364; the coin
stayed within 0.03 of zero. Telling them apart at 3σ needs about (3/(1−2e)ⁿ)² shots. At e = 1% that is 13.5 at
n = 10, 512 at n = 100 and 3.2×10¹⁸ at n = 1000.

## 3. At infinity

On every finite set of qubits the two states agree exactly, so on every quasi-local observable (finitely
supported, or a norm limit of such) the infinite cat and the coin give identical statistics. All-0 and all-1
lie in different superselection sectors: no quasi-local operator connects them, and the "superposition" is
a mixture. This is the standard algebraic result (e.g. Bratteli and Robinson), the same mechanism as
spontaneous symmetry breaking. The page states it and does not compute it. At infinity, *both* becomes
*either*.

## 4. The same fact, put to work

On a distance-d surface code, the page enumerates every X-type operator of weight w ≤ d. It keeps the
*silent* ones, which commute with every Z check, and counts those that flip the stored answer:

| d | weight | X operators | silent | flip the answer | straight columns |
| --- | --- | --- | --- | --- | --- |
| 3 | 1, 2 | 9, 36 | 0, 2 | 0, 0 | |
| 3 | 3 | 84 | 8 | 8 | 3 |
| 5 | 1–4 | 25 … 12,650 | 0, 4, 0, 22 | 0 | |
| 5 | 5 | 53,130 | 52 | 52 | 5 |
| 7 | 1–6 | 49 … 13,983,816 | 0, 6, 0, 47, 0, 251 | 0 | |
| 7 | 7 | 85,900,584 | 296 | 296 | 7 |

d = 3 and 5 run on load. d = 7 runs on a button and took 2.9 s in Chromium. No operator lighter than d
reaches the answer. Every weight-d answer-flipper crosses the grid touching each row exactly once, and only
d of them are straight columns. At weight d, every silent operator flips the answer.

**A correction before commit.** My first draft said "all of them are full lines across the grid", and the
first version of the load check only tested that the *first* flipper found was a straight column. Adding a
count of how many are straight showed that most zig-zag (8 at d = 3, of which 3 are straight). The text and
check now say what was actually found.

As d → ∞, no finite action reaches the stored answer. The fact that turns the cat into a coin is what makes
the code's answer permanent: what no finite part holds, no finite act can change.

## Checks

The page runs 10 checks on load. All pass in Chromium, with 0 console errors and 0 network requests.
`tests/test_infinite_cat.cjs` runs 4 Node tests on the same engine.

## What this is not

A finite page can't hold infinitely many qubits. Sections 1, 2 and 4 are exact finite computations whose
pattern is proved in general, and section 3 is the theorem they point to. "Every measurement is quasi-local" is
a statement about what is physical: global observables that tell the states apart can be written down, but
none has a finite approximation that does. Real cats are not GHZ states, and decoherence selects sectors only
approximately. The census covers X-type operators; Z-type follows by the code's symmetry.
