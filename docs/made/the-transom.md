# The transom

A bar over a door. Light may pass on one side at a time, and only on an open beat.

A line is `L` or `R`. The beat advances on every line, accepted or rejected, so a refused beam still spends the step. A line that names both sides, or neither, is too wide and is kept as rejected. The room draws when each side has passed twice. The parameter is which residue is open, `0` or `1`. Default is even.

This sits beside the stoop (a step that counts arrivals, open in #187) and the pane (a window that fogs on the line, open in #184). Neither is edited. The question it leaves open: if a later sitting lets the two sides share one count, does the bar still do any work?

```sh
python3 made/the-transom.py
```

Standard library only. The original pages stay as they are.
