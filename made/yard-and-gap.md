# Yard and gap

Noise Lab seed `grok-1006-third-sitting`, index 0. Ingredients: a flock and a maze. Constraint: a small example and a counterexample. Accepted.

Four birds, the same steering in both panels. They bounce when the next cell is a wall. They do not see each other.

- Example: the yard is closed. The probe bird is still inside after 80 steps.
- Counterexample: the east wall is missing the cell at row 4. The same probe leaves.

Not `flock-outside.html` and not `flock-in-a-maze.html`. Those already answer nearby draws. This page only shows that the rule does not know about the gap.

Three checks on load. No dependencies.
