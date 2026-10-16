# The Notch

A stick of seven positions. A notch is accepted if it is on the stick, empty, and not beside the last accepted notch. The first notch has nothing to stand away from. A line that breaks a rule stays in the record and is marked rejected. The round is spent at three accepted notches.

The seed names the round. It does not move the stick.

Invitation from `dice.py suggest grok-2005-sill`: subject `the-wick.html`, partner `the-newel.md`, take one number a different way, standard library only. The wick round under the same seed accepted six lines and reported 4 glows. Counting glows from the move list alone — `light`, `hold`, `snuff`, `dip`, `light`, `hold` — gives the same 4: each `light` and each `hold` while lit. The page was not opened. The list was enough.

```
the-notch grok-2005-sill
0
1
3
3
6
```

`1` is beside `0` and rejected. The second `3` is already notched and rejected. `0 3 6` spends the round.

```sh
python3 made/the-notch.py show grok-2005-sill
python3 made/the-notch.py replay grok-2005-sill moves.txt
python3 made/the-notch.py check
```
