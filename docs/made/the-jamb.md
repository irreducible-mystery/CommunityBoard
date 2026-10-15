# The jamb

A door frame with two sides. A knock is `L` or `R`. It is accepted only on
the open beat, and only on the jamb that did not take the previous accepted
knock. The first accepted knock may be either side. The beat advances on
every line, so a refused knock still spends the step. The door draws when
each jamb has taken two knocks. An off-beat knock, a same-side repeat, or a
word that is not `L` or `R` is kept and marked rejected. It is not removed.

Default open beat is the even one. `open_on` 1 flips it.

Standard library only. The games it sat beside stay as they are.

```
python3 made/the-jamb.py check
```
