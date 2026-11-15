# Jumps

*The program behind the notes [Where the jump goes](../posts/2026-11-15-where-the-jump-goes.md).*

The notes ask where the discontinuity goes when a logic lets sentences mention themselves. `jumps.py` does not prove them. It recomputes every result they mark `[computed]`, and it tries the claims they mark `[derived]` on examples, with a control beside each family of checks so that no check can pass by being empty.

```sh
python3 made/jumps.py       # 28 checks, about five seconds
python3 made/jumps.py -v    # the same, with the tables
```

What the six sections do:

- **A. Curry's sentence.** "If this sentence is true then A", valued in three logics with exact fractions: no value in Gödel–Dummett logic, the square root of a in product logic except at the liar, and (1 + a)/2 in Łukasiewicz logic. Close the graph of the first logic's "if" and the sentence gets exactly one value, a.
- **B. Once and twice.** Two Łukasiewicz sentences that differ only in using one clause twice. The first has one value except at a single state of the world. The second has three values between a = 1/2 and a = 2/3, one of them running backwards, so it leaps at 2/3 on the way up and at 1/2 on the way down. Of 106 small sentences that mention themselves twice, 24 fold like this. Of 103 that mention themselves once, none does.
- **C. The latch.** Six conditionals that obey two laws: if x is no truer than y then "x implies y" is fully true, and "true implies false" is fully false. In every one, a sentence built from "if" alone reads 0 after a reset and 1 after a set, at the same state of the world. Two conditionals that each drop one law read the same both ways. With min and max, 100 random amplifiers all give a latch and 100 random non-amplifiers give none.
- **D. No jump.** 200 random sentences built from "if", min and max. With either of the two blunt conditionals none jumps. With Łukasiewicz's, 17 of the same 200 do.
- **E. Off the line.** Pairs of truth values, with a conditional that mixes the two coordinates. The same latch, reading (0, 0) after reset and (1, 1) after set.
- **F. Counting.** "For some n: not R, n times over" has the value N/(N + 1) when the count stops at N, for N from 1 to 200, and no value at all when it does not stop.

Standard library only. No network, no files written. Exit status 0 when every check passes, 1 otherwise. Sections A, B, D and F use exact arithmetic or only the four operations, and the random sentences come from SHA-256 in counter mode, so they print the same on every machine. Sections C and E use sines and powers, so the tables shown by `-v` can differ in their last digits; the checks assert only what has to hold.

What a pass does not show: that the proofs in the notes are right, or that the notes' accounts of other people's theorems are right. The proofs are on the page to be read. The accounts are tagged `checked` or `recall` in the notes, with links.
