# Tetralemma, approaching infinity: four ways to grow

Companion to [`tetralemma-infinity.html`](tetralemma-infinity.html). SuperNinja session, 2026-10-05.
This is the second of three pages after the user asked, "What happens with zero qubits? What happens approaching
zero qubits? What happens with infinite qubits? What happens approaching infinite qubits?", and then said "All
please!" The others are `tetralemma-0.html` (PR #84) and `infinite-cat.html` (separate PR).

"As n goes to infinity" has no single answer: it depends which states you grow. The page follows four
families using closed forms, and checks each one against brute force wherever brute force fits in a browser.

| family | as n → ∞ | what happens to *neither* |
| --- | --- | --- |
| GHZ (the cat) | coherence (1−2q)ⁿ → 0 for any noise q > 0 | held by everyone together, so lost when anyone is touched |
| random states | half-cut gap → 1/(2 ln 2) = 0.7213 bits; small parts → 0 | almost perfect and almost free, never exact |
| symmetric (Dicke) | best pair concurrence 2/n → 0 | shared by everyone equally, so no pair holds any |
| repetition code | failure → 0 below p = ½, → 1 above | the curve sharpens into a step |

## 1. The cat gets fragile

GHZₙ keeps its "both" in one off-diagonal element. Independent phase flips with probability q multiply that
element by (1−2q) once per qubit. On load the page checks the closed form against the exact sum over all 2ⁿ
flip patterns for n ≤ 12. At q = 1%, the coherence is 0.980 (n = 1), 0.817 (10), 0.133 (100) and 1.7×10⁻⁹
(1000), and it halves by n ≈ 34. Keeping half the coherence at n = 10⁶ requires q < 3.47×10⁻⁷ ≈ ln 2/(2n).

## 2. Random states get almost perfect

Page's formula gives the mean entanglement entropy of k qubits of a Haar-random n-qubit state. The gap below
the maximum (k bits), for the half cut:

| n | 2 | 4 | 6 | 8 | 10 | 12 | 16 | 20 | 30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gap (bits) | 0.5191 | 0.6693 | 0.7082 | 0.7181 | 0.7205 | 0.7211 | 0.7213 | 0.72135 | 0.721348 |

The limit is 1/(2 ln 2) = 0.7213475 bits: the half cut never closes. A fixed part closes its gap
exponentially, roughly 2^(2k−n)(1−4^(−k))/(2 ln 2). For one qubit the gap is 2.1×10⁻³ at n = 10, 2.1×10⁻⁶ at 20
and 2.0×10⁻¹² at 40. So every small part looks perfectly scrambled, and the state as a whole is almost
perfect, never exactly (the seven-qubit page proves exact perfection impossible from n = 7). The engine uses
an Euler–Maclaurin tail for large N and is checked against the direct harmonic sum to 10⁻⁹ for n ≤ 22.
One correction from development is worth recording. My first version of that tail had the sign of the 1/(2a)
and 1/(2b) terms reversed. A scratch probe caught it: the half-cut gap fell from n = 30 to n = 40 (0.7213475 to 0.7213461) when it
should rise, and the one-qubit gap at n = 30 came out 6.7×10⁻¹⁰ instead of the asymptotic 2.0×10⁻⁹.

A sampling button draws seeded random states (n = 4 to 14) and compares their mean half-cut purity with
Lubkin's formula (m+N)/(mN+1). The load check requires agreement within 5% at n = 6, 8 and 10 (it got
0.2393/0.2462, 0.1258/0.1245 and 0.0626/0.0624). Gaps measured from purity are Rényi-2 gaps, which tend to
1 bit rather than 0.72, and the page says so.

## 3. Symmetric states share themselves away

For the Dicke state D(n, k), the two-qubit reduced state is an X-state with concurrence
2(k(n−k) − √(k(k−1)(n−k)(n−k−1)))/(n(n−1)). The page checks this formula against the explicit state vector for
every k at n ≤ 10. The best is k = 1 (the W state) with exactly 2/n: 1, 0.667, 0.5, 0.25, 0.125, 0.031 and 0.002
for n = 2, 3, 4, 8, 16, 64 and 1000. At k = n/2 it is 1/(n−1). Each qubit can still be strongly entangled with
the rest as a whole (tangle 4(k/n)(1−k/n), which is 1 at the half), but by monogamy (Coffman, Kundu and Wootters)
the shares must be small. The limit is the quantum de Finetti theorem: any two qubits of a symmetric state are
unentangled in the limit.

## 4. Repair gets sharp

Majority vote over d copies fails when more than d/2 flip:

| d | p = 0.1 | 0.3 | 0.45 | 0.55 | 0.7 |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1 | 0.3 | 0.45 | 0.55 | 0.7 |
| 3 | 0.028 | 0.216 | 0.425 | 0.575 | 0.784 |
| 11 | 3.0×10⁻⁴ | 0.078 | 0.367 | 0.633 | 0.922 |
| 101 | 1.2×10⁻²⁴ | 1.3×10⁻⁵ | 0.156 | 0.844 | ≈1 |
| 1001 | 8.0×10⁻²²⁵ | 3.6×10⁻⁴⁰ | 7.6×10⁻⁴ | 0.999 | ≈1 |

At p = ½ it is exactly ½ for every d. At infinity the curve is a step. The surface code (`surface-code.html`)
has the same kind of step for both quantum error types, near 10%.

The last load check first failed for a reason worth recording. I had required d = 1001 at p = 0.7 to be within
10⁻³⁰ of 1. In double precision, 1 − 3.6×10⁻⁴⁰ is 1 but the computed value was 0.9999999999997 (from
summing many terms in log space). I loosened it to 10⁻⁹ and added a symmetry check instead:
fail(d, 0.7) = 1 − fail(d, 0.3). The page-gap check also first failed: I had required the value at n = 64 to sit
strictly below the limit, but it equals the limit to within 2×10⁻¹⁶. The check now asks for agreement within
10⁻¹², and for the value at n = 32 to be strictly below the limit.

## Checks

The page runs 10 checks on load. All pass in Chromium, with 0 console errors and 0 network requests.
`tests/test_tetralemma_infinity.cjs` runs 5 Node tests on the same engine.

## What this is not

These are four families, not all states, and the limits here are limits of numbers computed at finite n.
The infinite system itself, where the mathematics changes, is on `infinite-cat.html`. The noise models are
the simplest independent ones; correlated noise matters most at large n. The random-state formulas are
averages. The repetition code handles only one kind of error.
