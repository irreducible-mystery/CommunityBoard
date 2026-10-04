# Tetralemma, six qubits: the last perfect corner

Companion to [`tetralemma-6.html`](tetralemma-6.html). Sequel to [two](tetralemma.md),
[three](tetralemma-3.md), [four](tetralemma-4.md) and five (`tetralemma-5.md`, PR #69, open when
this was written). SuperNinja session, 2026-10-04. The user asked to "continue tetralemma series with 6 qubits."

## What changes at six

**The last perfect corner.** A state is *absolutely maximally entangled* (AME) when every part of
at most half the qubits is maximally mixed. For qubits, such states exist for n = 2, 3, 5 and 6
only. They do not exist for 4 (Higuchi and Sudbery 2000), for 7 (Huber, Gühne and Siewert 2017),
or for 8 and more (Scott 2004). At six, the *neither* reaches half: any three qubits are
maximally entangled with the other three. That is 31 cuts (6 + 15 + 10), all at their maximum.

| state | 1\|5 at max | 2\|4 at max | 3\|3 at max | perfect |
| --- | --- | --- | --- | --- |
| \|000000⟩ | 0/6 | 0/15 | 0/10 | no |
| GHZ₆ | 6/6 (all exactly 1) | 0/15 (all 1) | 0/10 (all 1) | no |
| ring of six | 6/6 | 15/15 | 6/10 (others 2) | no |
| wheel (pentagon ABCDE + hub F) | 6/6 | 15/15 | 10/10 | yes |
| five-qubit code + witness | 6/6 | 15/15 | 10/10 | yes |

The ring of six fails on four 3|3 cuts: the three that take three neighbours (ABC|DEF, BCD|EFA,
CDE|FAB), and the alternating one (ACE|BDF). Being symmetric on a circle is not enough. A hub joined to all of a pentagon is.

**The ownerless answer gets a witness.** `(|0_L⟩|0⟩ + |1_L⟩|1⟩)/√2`: the five-qubit code from page
five with a sixth qubit F maximally entangled with the stored answer. It is perfect. What page
five stored as a value, held by no part, is here a relation between F and the code.

**The threshold.** For disjoint groups X and Y, I(X:Y) = S(X) + S(Y) − S(XY). In a perfect six the
values follow from the cut entropies alone, and the page checks them for the wheel:

| \|X\| | \|Y\| | together | I(X:Y) | cap 2·min |
| --- | --- | --- | --- | --- |
| 1 | 1 | 2 | 0 | 2 |
| 1 | 2 | 3 | 0 | 2 |
| 1 | 3, 4, 5 | 4–6 | 2 | 2 |
| 2 | 2 | 4 | **2** | 4 |
| 2 | 3, 4 | 5–6 | 4 | 4 |
| 3 | 3 | 6 | 6 | 6 |

Up to half, parts share nothing. Above half, they share the maximum, with one exception: two
disjoint pairs share 2 of a possible 4 bits, because the four of them keep 2 bits with the
remaining two. My first draft of the page said "everything above half"; the computed table
corrected it before the page was committed.

**Ask one qubit.** If any qubit of the wheel is measured, in Z or X with either outcome, the
other five are a perfect five (48 seeded questions on load, all perfect). Asking F of the witness
state "is it?" also leaves a perfect code state. Asking A of the ring of six leaves a five that is
not perfect. **Correction recorded here:** the first draft predicted that the wheel's rim and hub
would differ, with rim measurements breaking perfection. The load check failed (`rim Z true`),
and I rewrote the claim. The truth is the more symmetric statement: in the perfect six, every
qubit can serve as a witness.

**Census.** Each labelled graph on n vertices gives a graph state, and its cut entropies are GF(2)
ranks of adjacency sub-blocks (Hein, Eisert and Briegel 2004). Every stabilizer state is a graph
state up to local unitaries, which leave entropies unchanged, so the census covers every
stabilizer state exactly:

| n | labelled graphs | perfect |
| --- | --- | --- |
| 2 | 2 | 1 |
| 3 | 8 | 4 |
| 4 | 64 | 0 |
| 5 | 1,024 | 132 |
| 6 | 32,768 | 132 |
| 7 | 2,097,152 | 0 (button; about 1.5 s in headless Chromium) |

These agree with the theorems where the census can reach, though the theorems are stronger
because they cover non-stabilizer states. I don't explain the 132/132 coincidence. One way to see
it: each perfect six gives perfect fives on measuring any vertex. I haven't checked whether that
makes the map a bijection on labelled graphs, so I leave it as an open question rather than state it.

## Measured on this page (headless Chromium, 2026-10-04)

Ten checks on load, each able to fail; all pass: wheel 31/31; witness 31/31; ring 3|3 min 2 with
6/10 at max; GHZ₆ every cut exactly 1; the wheel's mutual-information table as above; 48 questions
on the wheel all leave a perfect five; ring question leaves an imperfect five; witness question
leaves a perfect code; census 1, 4, 0, 132, 132; GF(2) rank agrees with the state vector for the
wheel. Seven-qubit census: 0 of 2,097,152. No page errors and no network requests. Load time is
about 0.15 s.

Record format `tetralemma-6/1`: state, per-qubit entropy and word, cut summary, `perfect`,
the mutual-information table, the last question and what it left, the census and check results,
and the last 40 operations. Seeds use the Noise Lab RNG.

## The series, at its end for qubits

Two qubits: *neither* is half a Bell pair. Three: the whole, or the pairs. Four: the kinds stop
being countable, and the perfect *neither* is impossible. Five: it returns and keeps an answer no
part has. Six: it reaches half, any qubit can be its witness, and then it stops. From seven on,
some group of up to half the qubits always keeps something of its own. For larger groups the
corner needs larger parts: AME states exist again for more parties with qutrits and beyond.

## What this is not

It is a toy, and an exact one. It is not a claim about conversations. The census is exhaustive
only over graph states (equivalently stabilizer states), and the impossibility results for all
states come from the cited theorems, not from this page. Not done, for whoever follows: qutrit
AME states, and the 132 = 132 question.
