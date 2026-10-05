# Tetralemma, many qubits: when perfection is almost free

Companion to [`tetralemma-many.html`](tetralemma-many.html). It follows [six](tetralemma-6.md) and
[seven](tetralemma-7.md). SuperNinja session, 2026-10-05. This is the second of three pages written
after the user asked "what happens as we continue to add qubits?" and then said "All three please".

## The question

Seven showed that no state is perfect, meaning no state has every group up to half maximally mixed.
From eight on, the counting bounds rule perfection out as well. This page asks what a state picked
completely at random gives you instead.

## What the page measures

**1. The shortfall per group size.** A seeded random state of n = 6 … 20 qubits (2²⁰ amplitudes is the
in-page limit) is drawn. For each k up to half, the page shows S(first k) and the shortfall k − S, next to
Page's exact mean (Page 1993): Σ_{j=N+1}^{mN} 1/j − (m−1)/(2N) nats for an m × N split with m ≤ N.
In bits, the mean shortfall is very nearly (m − 1/m)/(2N ln 2). That is 2^{2k−n}(1 − 4^{−k})/(2 ln 2),
which agrees with the exact formula to better than 0.1% at n = 20 for every k. At half, m = N, and it gives
1/(2 ln 2) = 0.7213.

One draw, seed `tetralemma`, n = 20 (headless Chromium, about 4.4 s):

| k | shortfall k − S | Page mean | ÷ previous |
| --- | --- | --- | --- |
| 1 | 1.8×10⁻⁶ | 2.1×10⁻⁶ | |
| 4 | 0.0002 | 0.0002 | |
| 6 | 0.0028 | 0.0028 | 4.09 |
| 7 | 0.0113 | 0.0113 | 4.03 |
| 8 | 0.0450 | 0.0451 | 4.00 |
| 9 | 0.1805 | 0.1803 | 4.01 |
| 10 (half) | 0.7214 | 0.7213 | 4.00 |

For the smallest groups, a single draw can differ from the mean by a large factor in relative terms
(at n = 12, k = 2, the step ratio printed is 96.6). The shortfall there is tiny either way, and the page says so.

**2. The constant at half.** The half cut for n = 6 … 20, one draw each. Even n settle at 0.72. Odd n
(⌊n/2⌋ against ⌈n/2⌉) settle at about 0.36, half as much, as the quadrupling rule predicts.

**3. Every triple.** For n ≤ 14, all C(n,3) triples are checked. At n = 12 with seed `tetralemma`, all 220
lie between 2.9796 and 2.9922 bits out of 3. At seven, no state reaches 3 on every triple. At twelve,
chance comes within 0.03 on every one.

**4. The cat and the crowd.** GHZ and a random state of the same size are asked "is it?" one qubit at a
time, with seeded answers. The cat's middle cut goes from 1 to 0 on the first answer and stays at 0. The
crowd loses about half a bit per answer and tracks Page's mean for the smaller random state. For n = 12:
5.277 → 4.649 → 4.283 → … → 1.330 with 4 left, against Page's 5.279, 4.640, 4.279, … 1.331.

## Numerics

Eigenvalues come from a complex Householder reduction to tridiagonal form followed by implicit QL. The
real 2d × 2d embedding used on the earlier pages was too slow for a 1024 × 1024 half cut. For the
shortfall at large N, Page's formula is evaluated through its Euler–Maclaurin tail, so that small
differences are not lost to cancellation. A load check confirms that it agrees with the direct sum.
Random states are i.i.d. complex Gaussians, normalised, seeded by FNV-1a → Mulberry32 as in noise-lab.

## Checks

There are 10 checks on load, and all pass. They cover:
- eigensolver identities;
- the two sides of a cut;
- the Page two-qubit mean against 400 seeded draws (0.4911 vs 0.4809);
- the 12-qubit shortfall range;
- the series against the direct sum, and the 1/(2 ln 2) limit;
- GHZ cuts, and GHZ after a question;
- the crowd after a question;
- all 220 triples at 12;
- normalisation at 16.

There are also 5 Node tests in `tests/test_tetralemma_many.cjs`. In headless Chromium there are no page errors and no network requests.

## A correction made before committing

My first draft of a load check compared S(first 3) with S(first 7) and expected them to be equal. They
are not, since those are different cuts. The correct identity is S(first 7) = S(last 3). The check failed,
I fixed the check, and the claim in the text was not affected. A second check failed because the plain
sum for Page's mean loses about 10⁻⁹ to cancellation at n = 40. That led to the series form described above.

## What this is not

Random states are not a model of a crowd of people. The toy is exact about a trade-off. Design reaches
perfection at 2, 3, 5 and 6 qubits and fails at 7. Chance never reaches it, but comes within a hair of it
everywhere except at half, where the gap is a fixed 0.72 bits.
