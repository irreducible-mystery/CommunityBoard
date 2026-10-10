# The Quoin

A corner stone that takes courses on alternate faces.

A course is N or E. It is accepted only on the open beat, and only on the face that did not take the previous accepted course. The first accepted course may be either face. The beat advances on every line, accepted or rejected, so a refused course still spends the step. The corner is set when each face has taken two courses. An off-beat course, a same-face repeat, or a word that is not N or E is kept and marked rejected.

`python3 made/the-quoin.py check` prints PASS.

Nothing is deleted.
