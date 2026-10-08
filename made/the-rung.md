# The Rung

A maze whose doors are word-ladder steps. Rooms are COLD, CORD, CARD, WORD, WARD, WARM. A door exists only where the two words differ by one letter. The parameter is which door is a wall, 0 through 4. Crossing a wall stays and is marked rejected.

Seed `grok-1008-eleventh`, Noise Lab index 0: a maze and a word ladder. Constraint: at most 100 lines. Standard library only.

`python3 made/the-rung.py` prints PASS. Wall 1 still reaches WARM by WORD. The walled CARD door is rejected. Wall 3 stops at WORD.
