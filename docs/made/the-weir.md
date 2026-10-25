# The Weir

Two streams and a gate. The gate opens only when they hold the same letter on the beat.

Off the beat: `left a`, `right b`, or `both a`. On the beat: `agree X`, and only if both streams already hold X. A line that breaks a rule stays and is marked rejected. The turn does not advance. The round is drawn at three passes.

The seed names the round. It does not change the rules.

```
python3 made/the-weir.py check
python3 made/the-weir.py replay grok-1009-weir moves.txt
```

Standard library only. A small example and a counterexample are in `check`.
