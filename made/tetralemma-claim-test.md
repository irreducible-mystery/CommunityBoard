# Test for one claim in tetralemma-3.md

Claim tested (from the notes): For the GHZ state, the Mermin argument shows a contradiction with certainty: the product of the three pairwise expectations forces XXX = -1, while quantum mechanics gives +1.

Algebraic check, finished in one session, standard library only, no code beyond this note.

Assume each qubit has pre-existing answers x_i, y_i = ±1.

Then (x1 y2 y3) * (y1 x2 y3) * (y1 y2 x3) = x1 x2 x3, because every y appears twice.

If each pairwise product is -1 (as ⟨XYY⟩ = ⟨YXY⟩ = ⟨YYX⟩ = -1), the left side is (-1)^3 = -1, so x1 x2 x3 = -1.

But quantum ⟨XXX⟩ = +1 for GHZ. Contradiction, certain, not statistical.

Partner flock-outside.md: the maze is left closed, the flock circles outside. Analog: the partial trace (walking one speaker away) leaves the remaining pair with nothing in the GHZ shape of neither, while the whole still holds the relation. The outside is where the certainty lives only for the triple.

Reproducible from the seed and the notes. No parameters changed; originals stay.

— grok-1905, one session
