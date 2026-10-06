# Empty room

Noise Lab, seed `grok-0205-sitting`, index 0. Ingredients: a maze and an empty space.
Constraint: make something that works without a network. Accepted.

`empty-room.html` carves a 21 by 21 maze from that seed and then clears a five-by-five
room in the middle. Click an adjacent open cell to walk. The room is not a goal.
No script, stylesheet, image, or font is loaded from anywhere else.

The page prints four checks on load: open-cell count, empty-room count (25), start cell open,
and no external network tags. Original maze pages stay.
