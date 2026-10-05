# Tetralemma, seven qubits: the impossible one

Companion to [`tetralemma-7.html`](tetralemma-7.html). It follows [two](tetralemma.md),
[three](tetralemma-3.md), [four](tetralemma-4.md), [five](tetralemma-5.md) and [six](tetralemma-6.md).
SuperNinja session, 2026-10-05. The user asked "what happens as we continue to add qubits?" and then
said "All three please". This is the first of three pages. The second covers many qubits at random,
and the third is a surface code.

## The claim

No pure state of seven qubits has all 35 of its three-qubit parts maximally mixed (Huber, Gühne and
Siewert, Phys. Rev. Lett. 118, 200502 (2017), arXiv:1608.06228). If every qubit and pair is
maximally mixed, at most 32 of the 35 triples can be, and a graph state reaches 32.

## What the page computes

| item | result | where |
| --- | --- | --- |
| best graph `AE AF AG BC BD BG CD CF DE` | qubits 7/7, pairs 21/21, triples 32/35, from the 128-amplitude state vector | load check 1 |
| its missing triples | ADE, ACF, ABG: all start at A, each a two-edge path out of A | section 2 |
| wheel (hexagon + hub) | also 32/35; ring of seven 28/35 | load check 3 |
| GF(2) cut rank vs. entropy | equal on all 63 cuts of three graphs | load check 2 |
| asking one qubit of the best graph (Z, i.e. vertex deletion) | the six left keep 26–33 of 41 cuts, never 41 | section 2 |
| census of all 2,097,152 labelled graphs (button, ~5.5 s in headless Chromium) | 620,640 have all qubits and pairs maximally mixed; 115,080 miss 3 triples and 505,560 miss 7; none miss 0, 1, 2, 4, 5 or 6 | section 3, Node test |
| five-sets usable by the proof, over all graphs | 0 | section 3, Node test |
| weight enumerator of the best graph | 1, 0, 0, 3, 29, 42, 34, 19 | load check 7 |
| summed triple purity, best graph | 4.75 = 32/8 + 3/4 (perfect would be 35/8 = 4.375) | load check 10 |
| gradient search, seed `tetralemma`, 800 steps | 6.3666 → 4.6183; triples all between 0.1276 and 0.1377, none exactly 1/8 | section 6 |

## The proof, in steps

1. In the Pauli-word (Bloch) expansion ρ = 2⁻ⁿ(1 + P₁ + … + Pₙ), a perfect seven has P₁ = P₂ = P₃ = 0.
2. **The parity rule:** if {M, N} is non-zero, its weight is |M| + |N| mod 2. The page checks this on
   random seven-letter Pauli words.
3. A five-qubit part is a rank-4 projector, ρ₅² = ¼ρ₅, with ρ₅ = 2⁻⁵(1 + Σⱼ P₄^[j] + P₅). The Schmidt
   decomposition gives P₄^[j]|φ⟩ = |φ⟩ for each of the five j, and P₅|φ⟩ = 2|φ⟩.
4. Collect the weight-5 (odd) terms of ρ₅². Only the cross term contributes, so
   {P₅, Σⱼ P₄^[j]} = 6 P₅.
5. Apply both sides to |φ⟩: 2·5·1 + 5·1·2 = 20 on the left and 6·2 = 12 on the right. Contradiction.

For a graph state these eigenvalues are counts of stabilizer words. The page lists the counts for
every four-qubit part of the perfect six, which has the value the method needs (3 words of weight 4
and none lower). It also lists them for every five-qubit part of the best seven, where no part
has the required "no low words, 1 1 1 1 1, and 2".

## Linear programming does not see it

If every part up to half is maximally mixed, the quantum MacWilliams identities fix the weight enumerator.

| n | forced A₀…Aₙ | shadow | verdict |
| --- | --- | --- | --- |
| 4 | 1, 0, 0, 12, 3 | −1/2, 0, 9, 0, 15/2 | excluded (shadow) |
| 5 | 1, 0, 0, 10, 15, 6 | 0, 0, 0, 20, 0, 12 | allowed (exists) |
| 6 | 1, 0, 0, 0, 45, 0, 18 | equal to A | allowed (exists) |
| 7 | 1, 0, 0, 0, 35, 42, 28, 22 | 0, 7/4, 0, 35/4, 0, 357/4, 0, 113/4 | **allowed** |
| 8 | 1, 0, 0, 0, 0, 168, −84, 168, 3 | −13/8, … | excluded (A₆ < 0) |

Seven passes, and so do the enumerators of its 5- and 6-qubit parts. So the counting tools alone
cannot exclude it. The parity rule is about how weights combine, and that is what they miss.
I computed these tables first with exact fractions in Python, and the page recomputes them in floating
point.

## Checks

10 on load, all passing in headless Chromium, with no page errors and no network requests. 7 Node
tests in `tests/test_tetralemma_7.cjs` run the page's engine (`<script id="t7-engine">`), including the
full 2²¹ census (about 7 s).

## What I got wrong on the way

My first description of the three missing triples was "A and its two neighbours". That is false:
A's neighbours are E, F and G, and the missing triples are ADE, ACF and ABG. I corrected it to
two-edge paths out of A before committing. An earlier draft also said that one usable five-set
"would have been enough to make a perfect seven". That is wrong too. A usable set would only have
meant the argument could be run there, and running it would then give the contradiction. The census
covers stabilizer states only and checks the theorem where it can reach. It does not replace the
theorem, and the page now says that.

## What this is not

A toy, exact in what it computes. It is not a claim about groups of people. It shows a well-posed
wish (every small group wholly bound up with the rest) that two, three, five and six can satisfy and
seven cannot, and it shows why.
