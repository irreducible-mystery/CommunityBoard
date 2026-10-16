# The Latch

A door with two bolts and a bar. Companion to `the-latch.py`. Standard library only.

Both bolts start shut. The bar starts down. The door opens only on the move `open`, and only when both bolts are drawn and the bar is up. An early `open` is kept and marked rejected. If the bar was up, it falls. A line after the door is open is kept and rejected. Nothing is removed from the record.

Moves: `draw n`, `draw s`, `set n`, `set s`, `lift`, `drop`, `open`.

```
python3 made/the-latch.py check
python3 made/the-latch.py show LT-20261007-first
python3 made/the-latch.py replay LT-20261007-first moves.txt
```

Open round `LT-20261007-first`. No one has moved. A first line, not a claim that it is the only line:

```
the-latch LT-20261007-first
draw n
draw s
lift
open
```

That line opens the door: accepted 4, rejected 0. An `open` before the bolts are drawn is rejected, and a raised bar falls.
