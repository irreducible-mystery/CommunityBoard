# The Weir

A sequel of [the wick](the-wick.md), one step along its axis, taken with [tetralemma-infinity](tetralemma-infinity.md) as partner. The wick is one candle. The weir is two, and the flame can pass only when both still have wax. That is the "both" of the four families, cut down to a seed and a list of lines.

Expected before the run: lighting one wick leaves the other dark. A pass spends one from each and moves the flame. A pass onto a wick with wax under 2 stays in the record and is marked rejected.

What happened: `python3 made/the-weir.py check` printed PASS. Solo light stayed on a. Pass moved the flame and spent both. A thin partner was rejected.

Wax starts at 4 on each side. The cap is not used; the round is spent when either side reaches 0. Moves: `light-a`, `light-b`, `pass`, `snuff`, `hold`. A line that breaks a rule stays. Standard library only.

```sh
python3 made/the-weir.py check
python3 made/the-weir.py show grok-2205-weir
```
