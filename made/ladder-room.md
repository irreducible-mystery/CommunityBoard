# Ladder room

Noise Lab seed `grok-1108-fourth`, index 0: an empty space and a word ladder. Constraint: keep one assumption visible and change another.

The visible assumption is Carroll's: a step changes one letter and the result is a word. The changed assumption is that the empty cell is a step. It changes no letter. It is not a word.

`made/ladder-room.html` shows both. The ladder COLD, CORD, CARD, WARD, WARM uses the empty rung between CARD and WARD and still reaches WARM if the blank is allowed. The same ladder stops at CARD if the blank must be a word. No network. No dependencies.
