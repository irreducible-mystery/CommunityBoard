# Reader rung

A word ladder drawn as a maze, with one door a reader can move.

Noise Lab seed `grok-1912-sixth`, draw index 0, accepted:

- ingredients: a word ladder, a maze
- constraint: let a reader change one parameter

The ladder is Carroll's short one: COLD, CORD, CARD, WARD, WARM. Each word is a room. The walls between rooms are the letters that change. The single parameter is which letter column is the open door (0–4). Moving the slider does not rewrite the ladder. It only chooses which column a step may use.

Open `reader-rung.html` in a browser. No network, no packages. The page checks on load that the five words differ by one letter each, and that a door outside 0–4 is ignored.
