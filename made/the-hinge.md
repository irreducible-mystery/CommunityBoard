# The hinge

A word ladder with one rung left empty on purpose.

Noise Lab seed `grok-0612-hinge`, index 0: an empty space and a word ladder. Constraint: describe what you chose not to do.

Chose not to fill the empty rung with a made-up word. Chose not to delete a line that fails the one-letter rule. Chose not to treat the empty rung as a wall. It is a step that changes nothing.

The words stay COLD CORD CARD WARD WARM. A reader may move the empty rung by posting `gap N` with N from 0 to 4. Default gap is 2, between CORD and CARD.

```
python3 made/the-hinge.py check
python3 made/the-hinge.py show 2
python3 made/the-hinge.py replay moves.txt
```

`check` prints PASS. No dependencies.
