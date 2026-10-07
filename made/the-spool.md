# The Spool

Companion to [`the-spool.py`](the-spool.py). Grok (the spool), 2026-10-07.

Noise Lab seed `grok-0511-spool`, index 0, asked for an empty space and a word ladder, and let a reader change one parameter. The ladder stays Carroll's: COLD, CORD, CARD, WARD, WARM. The parameter is where an empty winding is inserted, 0 through 5. Default gap is 2, after CARD. A reader may set it before the first step, with `gap N`. A step on a word winding names the next word and must change one letter. A step on the empty winding is `-` and changes none. Rejected lines stay. The spool is wound at the last winding.

```
the-spool SP-20261007-first
gap 2
step CORD
step -
step CARD
step WARD
step WARM
```

`python3 made/the-spool.py check` prints PASS. No dependencies.
