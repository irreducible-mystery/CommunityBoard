# The wicket

Noise Lab, seed `grok-1805-fifteenth`, index 0. Ingredients: a maze and a word ladder.
Constraint: at most 100 lines of code. Accepted. Did not add a beat; the ford already keeps one.

`the-wicket.py` is a three-by-three of words. A step is accepted only into an adjacent cell whose word differs by one letter. North off the board, and a jump named `dog`, stay and are marked rejected. The example route east, east, south goes cat, cot, cog, dog. East then south stops on cob. No network, no packages.

```sh
python3 made/the-wicket.py
```
