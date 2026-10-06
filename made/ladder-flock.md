# Ladder flock

Noise Lab, seed `grok-0305-sitting`, index 0.

The draw was a word ladder and a flock. The constraint was: make a small example and a counterexample.

Accepted as a page, not as a change to `doublets.html` or `ladder-with-a-hole.html`. Those stay.

## Example

Four birds, one letter each. A legal step moves exactly one bird to a neighbouring letter. `COLD` → `CORD` → `CARD` → `WARD` → `WARM`. Each step has Hamming distance 1. After four steps the flock spells WARM.

## Counterexample

The same four birds are asked to become `WARM` in one step. Four letters differ. The rule refuses the step. The word stays `COLD`. A flock is not a teleport.

Not done: a dictionary, a solver, a score, a server.
