# The Quay

A dock. Noise Lab seed `grok-1908-quay`, index 0: a rhythm and a word ladder.
Constraint: a small example and a counterexample.

The tide starts high and turns only after an accepted boat. A skiff is taken
on high water. A barge is taken on low water. A line that disagrees stays and
is marked rejected, and the tide does not turn.

Example:

```
SKIFF
BARGE
SKIFF
BARGE
```

Counterexample: `BARGE` on the opening high. The line is kept. The tide stays high.

```sh
python3 made/the-quay.py check
```

Prints `PASS`. No dependencies.
