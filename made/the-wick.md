# The Wick

A candle of seven, played by lines. Sessions do not share a clock, so the round is a seed plus an ordered list of moves. Anyone can replay the list and get the same wick.

Wax starts at 4. The cap is 7. `dip` adds one if the wick is dark and under the cap. `trim` takes one if the wick is dark and longer than 1. `light` is only legal when dark and the wax is at least 2: it lights the wick and burns one, which counts as a glow. `snuff` puts a lit wick out. `hold` burns one more if lit, and changes nothing but the turn if dark. A line that breaks a rule stays in the record and is marked rejected. The field is unchanged by it.

The round is spent when the wax reaches 0 or the glows reach 5. Spending the wax is not failure of the record. It is one way the round can end.

```
the-wick grok-1407-wick
light
hold
snuff
dip
light
```

Six checks. Standard library only. The page follows the same moves.

```sh
python3 made/the-wick.py show grok-1407-wick
python3 made/the-wick.py replay grok-1407-wick moves.txt
python3 made/the-wick.py check
```
