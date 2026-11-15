# Observers

*The program behind the notes [Sameness on a budget](../posts/2026-11-15-sameness-on-a-budget.md).*

The notes propose a mathematics in which "equal" means "no test this observer can afford tells them apart". `observers.py` does not prove them. It recomputes every number they mark `[computed]`, and it checks the laws they mark `[derived]` on examples and on 200 random finite models, with a negative control beside each law so that no check can pass by being empty.

```sh
python3 made/observers.py       # 26 checks, about four seconds
python3 made/observers.py -v    # the same, with the tables
```

What the six sections do:

- **A. Coins.** How well the best possible test tells two coins apart after 10 to 1,000,000 flips, and how many flips it takes to be right three times in four: 45, 4,549 and 454,936 for coins that differ by 10, 1 and 0.1 points.
- **B. Parity.** Strings with an even or an odd number of 1s are identical to every test that reads fewer than all the bits, and completely different once someone computes the parity.
- **C. Several observers.** Remainders mod 4 and mod 25 pin down every number from 0 to 99; mod 10 with mod 20 promise 200 distinctions and deliver 20.
- **D. Primes as observers.** The product formula, exactly, for 2000 random fractions, and the fact that prime observers never leak along a chain while ordinary size does.
- **E. The calculus.** The five rules on 200 random finite models. The leak-free chain rule fails in 192 of them and free substitution in 195, which is what the rules say should happen.
- **F. A weak real observer.** zlib charges for a random string and its reversal as two strings' worth of information until the reversal is undone.

Standard library only. No network, no files written. Exit status 0 when every check passes, 1 otherwise. Randomness comes from SHA-256 in counter mode, so the numbers are the same on every machine; section F uses zlib and asserts only bounds.

What a pass does not show: that the notes' accounts of other people's theorems are right. Those are tagged `checked` or `recall` in the notes, with links.
